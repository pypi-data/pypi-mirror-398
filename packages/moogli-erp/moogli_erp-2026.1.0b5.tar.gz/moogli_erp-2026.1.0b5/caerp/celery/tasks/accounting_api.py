import datetime
import time

import requests
import transaction
from pyramid_celery import celery_app
from sqlalchemy import delete, insert, select

from caerp import version as caerp_version
from caerp.celery.conf import get_recipients_addresses, get_request, get_setting
from caerp.celery.tasks import utils
from caerp.models.accounting.operations import (
    AccountingOperation,
    AccountingOperationUpload,
)
from caerp.models.company import Company
from caerp.utils.mail import send_mail

logger = utils.get_logger(__name__)


MAIL_SUCCESS_SUBJECT = "[SUCCÈS] Remontée comptable terminée"

MAIL_SUCCESS_BODY = """La remontée comptable s'est terminée avec succès !

Vos états comptables n'ont pas été automatiquement mis à jour.
Pensez à les re-générer manuellement depuis l'application si besoin.
"""

MAIL_ERROR_SUBJECT = "[ERREUR] Échec de la remontée comptable"

MAIL_ERROR_BODY = """Une erreur est survenue lors de la remontée comptable.

Vos états comptables ne seront pas mis à jour pour ne pas les fausser, mais 
les écritures visibles dans l'application (depuis le grand livre par exemple) 
pourraient être incomplètes.

Si le problème persiste, veuillez contacter votre administrateur en lui
transmettant le message d'erreur suivant :

    {error_message}
"""


class QuadraOnDemandApiHandler:

    base_url = "https://www.quadraondemand.com/QuadraODOpenApi"
    auth_url = f"{base_url}/token"
    accounting_url = f"{base_url}/api/v1/comptabilite/ecritures_analytique"
    auth_token = None
    analytical_accounts_cache = {}
    accounting_upload_cache = {}
    used_upload_ids = []
    items_per_page = 5000
    max_attempt = 15
    retry_delay = 30  # in seconds
    attempt = 1

    def __init__(self, request):
        self.request = request
        self.mail_addresses = get_recipients_addresses(self.request)
        self._get_ini_config()

    def _get_ini_config(self):
        try:
            self.client_id = get_setting("caerp.quadraod_client_id", mandatory=True)
            self.client_secret = get_setting(
                "caerp.quadraod_client_secret", mandatory=True
            )
            self.vendor_name = get_setting("caerp.quadraod_vendor_name", mandatory=True)
            self.file_id = get_setting("caerp.quadraod_file_id", mandatory=True)
        except Exception as err:
            raise Exception(
                "QuadraOnDemand configuration missing, expecting : \
quadraod_client_id, quadraod_client_secret, quadraod_vendor_name, quadraod_file_id"
            )

    def _cache_companies_analytical_accounts(self):
        for company in Company.query(active=False).order_by(Company.id):
            if company.code_compta not in self.analytical_accounts_cache:
                self.analytical_accounts_cache[company.code_compta] = company.id

    def _cache_accounting_uploads(self):
        for upload in AccountingOperationUpload.query().filter_by(
            filetype=AccountingOperationUpload.SYNCHRONIZED_ACCOUNTING
        ):
            self.accounting_upload_cache[upload.date.year] = upload.id

    def _get_or_create_upload_id(self, date_object):
        upload_id = self.accounting_upload_cache.get(date_object.year)
        if not upload_id:
            upload = AccountingOperationUpload(
                date=datetime.date(date_object.year, 1, 1),
                filetype=AccountingOperationUpload.SYNCHRONIZED_ACCOUNTING,
                filename="Écritures {}".format(date_object.year),
            )
            self.request.dbsession.add(upload)
            self.request.dbsession.flush()
            self.accounting_upload_cache[date_object.year] = upload.id
            upload_id = upload.id
        return upload_id

    def _prepare_accounting_uploads(self, limit_date=datetime.date(1970, 1, 1)):
        logger.debug("Marking all concerned accounting uploads as unvalid...")
        first_concerned_upload = self.request.dbsession.execute(
            select(AccountingOperationUpload)
            .where(AccountingOperationUpload.date <= limit_date)
            .order_by(AccountingOperationUpload.date.desc())
        ).scalar()
        if first_concerned_upload:
            self.used_upload_ids.append(first_concerned_upload.id)
            first_concerned_upload.is_upload_valid = False
            self.request.dbsession.merge(first_concerned_upload)
        other_concerned_uploads = self.request.dbsession.execute(
            select(AccountingOperationUpload).where(
                AccountingOperationUpload.date > limit_date
            )
        ).scalars()
        for concerned_upload in other_concerned_uploads:
            self.used_upload_ids.append(concerned_upload.id)
            concerned_upload.is_upload_valid = False
            self.request.dbsession.merge(concerned_upload)
        transaction.commit()
        transaction.begin()

    def _update_used_accounting_uploads(self):
        logger.debug("Updating used accounting uploads...")
        for upload_id in self.used_upload_ids:
            upload = self.request.dbsession.execute(
                select(AccountingOperationUpload).where(
                    AccountingOperationUpload.id == upload_id
                )
            ).scalar()
            if upload:
                upload.updated_at = datetime.datetime.now()
                upload.is_upload_valid = True
                self.request.dbsession.merge(upload)
        self.used_upload_ids = []
        transaction.commit()
        transaction.begin()

    def _delete_existing_operations(self, limit_date=datetime.date(1970, 1, 1)):
        logger.info(
            "Deleting existing accounting operations from {}...".format(
                limit_date.strftime("%Y-%m-%d")
            )
        )
        self.request.dbsession.execute(
            delete(AccountingOperation).where(AccountingOperation.date >= limit_date)
        )
        transaction.commit()
        transaction.begin()

    def _api_authorize(self):
        try:
            logger.debug(f"Requesting bearer token from {self.auth_url}")
            api_response = requests.post(
                self.auth_url,
                data=dict(
                    grant_type="client_credentials",
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    vendor_name=self.vendor_name,
                    application_name="CAERP",
                    application_version=caerp_version(),
                ),
            )
            assert api_response.status_code == 200
            json_api_response = api_response.json()
            assert "access_token" in json_api_response
            self.auth_token = json_api_response["access_token"]
            logger.debug("Bearer token received !")
            self.attempt = 1
            return True
        except Exception as error:
            logger.error(
                "QuadraOnDemand AUTH server exception - Attempt {} / {}".format(
                    self.attempt,
                    self.max_attempt,
                )
            )
            logger.error(error)
            self.attempt += 1
            if self.attempt > self.max_attempt:
                # Fatal error - No more retry attempts
                raise Exception(
                    "[FAILED] QuadraOnDemand AUTH server is not available : {}".format(
                        error
                    )
                )
            else:
                # Retry fetching operations after delay
                time.sleep(self.retry_delay)
                return self._api_authorize()

    def _api_fetch_operations(self, page=1):
        try:
            url = "{}?numeroDossier={}&maxPage={}&numeroPage={}".format(
                self.accounting_url,
                self.file_id,
                self.items_per_page,
                page,
            )
            headers = dict(Authorization=f"Bearer {self.auth_token}")
            api_response = requests.post(url, headers=headers)
            assert api_response.status_code == 200
            json_api_response = api_response.json()
            assert "EcritureDate" in json_api_response["Data"][0]
            logger.debug(
                "Successfully fetch {} operations from API (page {}/{})".format(
                    min(self.items_per_page, json_api_response["NbElement"]),
                    page,
                    json_api_response["NbPage"],
                )
            )
            self.attempt = 1
            return json_api_response
        except Exception as error:
            logger.error(
                "QuadraOnDemand API server exception - Attempt {} / {}".format(
                    self.attempt,
                    self.max_attempt,
                )
            )
            logger.error(error)
            self.attempt += 1
            if self.attempt > self.max_attempt:
                # Fatal error - No more retry attempts
                raise Exception(
                    "[FAILED] QuadraOnDemand API server is not available : {}".format(
                        error
                    )
                )
            else:
                # Retry fetching operations after delay
                time.sleep(self.retry_delay)
                return self._api_fetch_operations(page=page)

    def _get_operations_metadata_from_api_response(self, api_response):
        try:
            min_op_date = None
            for op in api_response["Data"]:
                op_date = datetime.datetime.strptime(op["EcritureDate"], "%d/%m/%Y")
                if not min_op_date or op_date < min_op_date:
                    min_op_date = op_date
        except Exception as e:
            raise Exception("Failed to compute first operation date : {}".format(e))
        try:
            return (
                api_response["NbElement"],
                api_response["NbPage"],
                min_op_date,
            )
        except Exception as e:
            raise Exception(
                "Missing metadata from QuadraOnDemand API response : {}".format(e)
            )

    def _format_operation_from_json(self, operation_json):
        ec_ana = operation_json["Centre"]
        ec_date = datetime.datetime.strptime(operation_json["EcritureDate"], "%d/%m/%Y")
        ec_compte = (
            operation_json["CompAuxNum"]
            if operation_json["CompAuxNum"] != ""
            else operation_json["CompteNum"]
        )
        ec_label = operation_json["EcritureLib"]
        if float(operation_json["Debit"]) == 0:
            ec_debit = 0
            ec_credit = operation_json["MontantAna"]
        else:
            ec_debit = operation_json["MontantAna"]
            ec_credit = 0
        company_id = (
            self.analytical_accounts_cache[ec_ana]
            if ec_ana in self.analytical_accounts_cache
            else None
        )
        upload_id = self._get_or_create_upload_id(ec_date)
        return {
            "id": None,
            "date": ec_date.strftime("%Y-%m-%d"),
            "analytical_account": ec_ana,
            "general_account": ec_compte,
            "label": ec_label,
            "debit": ec_debit,
            "credit": ec_credit,
            "balance": ec_debit - ec_credit,
            "company_id": company_id,
            "upload_id": upload_id,
        }

    def _store_operations(self, operations_data):
        logger.info(f"Storing {len(operations_data)} operations ...")
        operations_to_insert = []
        for json_op in operations_data:
            operations_to_insert.append(self._format_operation_from_json(json_op))
        self.request.dbsession.execute(
            insert(AccountingOperation), operations_to_insert
        )
        transaction.commit()
        transaction.begin()

    def _send_success_by_mail(self):
        if self.mail_addresses:
            try:
                send_mail(
                    self.request,
                    self.mail_addresses,
                    MAIL_SUCCESS_BODY,
                    MAIL_SUCCESS_SUBJECT,
                )
            except Exception as err:
                logger.exception(
                    "Failed to send success to {} : {}".format(self.mail_addresses, err)
                )

    def _send_error_by_mail(self, error):
        if self.mail_addresses:
            try:
                send_mail(
                    self.request,
                    self.mail_addresses,
                    MAIL_ERROR_BODY.format(error_message=str(error)),
                    MAIL_ERROR_SUBJECT,
                )
            except Exception as err:
                logger.exception(
                    "Failed to send error to {} : {}".format(self.mail_addresses, err)
                )

    def synchronize_accounting(self):

        try:

            # Prepare cache
            self._cache_companies_analytical_accounts()
            self._cache_accounting_uploads()

            # Authenticate
            self._api_authorize()

            # Fetch operations
            page_num = 1
            logger.info(f"Fetching accounting operations page {page_num} ...")
            api_response = self._api_fetch_operations(page_num)
            (
                nb_operations,
                nb_pages,
                first_op_date,
            ) = self._get_operations_metadata_from_api_response(api_response)
            logger.debug(f"{nb_operations} operations will be sync on {nb_pages} pages")
            self._prepare_accounting_uploads(first_op_date)
            self._delete_existing_operations(first_op_date)
            self._store_operations(api_response["Data"])
            while page_num < nb_pages:
                page_num += 1
                logger.info(
                    f"Fetching accounting operations page {page_num} / {nb_pages}..."
                )
                api_response = self._api_fetch_operations(page_num)
                self._store_operations(api_response["Data"])

            # Update accounting uploads
            self._update_used_accounting_uploads()

        except Exception as err:

            logger.error(err)
            logger.error("Synchronization failed !")
            self._send_error_by_mail(err)

        else:

            logger.info(f"Synchronization succeed with {nb_operations} operations !")

            # Send success mail if daytime
            current_hour = int(datetime.datetime.now().strftime("%H"))
            if current_hour >= 7 and current_hour < 22:
                self._send_success_by_mail()


@celery_app.task(bind=True)
def synchronize_accounting_from_quadraod(self, request=None):

    if not request:
        request = get_request()
    handler = QuadraOnDemandApiHandler(request)
    handler.synchronize_accounting()

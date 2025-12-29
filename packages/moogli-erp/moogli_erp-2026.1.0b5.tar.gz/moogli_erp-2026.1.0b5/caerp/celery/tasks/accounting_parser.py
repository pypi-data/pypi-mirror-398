# -*- coding: utf-8 -*-
"""
Accounting operations parsing

Parses :

    csv files
    slk files

- Collect the administration mail address
- Inspect the pool for waiting files
- Find the parser and the filetype
- Parse
    - Collect file informations
    - Ensure we have csv datas
    - Insert lines in database

"""
import datetime
import os
from pathlib import Path
from typing import List, Optional, Tuple

import transaction
from dateutil.relativedelta import relativedelta
from pyramid_celery import celery_app
from sqlalchemy import distinct

from caerp.celery.conf import get_recipients_addresses, get_request, get_setting
from caerp.celery.exception import FileNameException
from caerp.celery.interfaces import IAccountingFileParser, IAccountingOperationProducer
from caerp.celery.parsers import BaseParser, BaseProducer, UploadMetaData
from caerp.celery.tasks import utils
from caerp.celery.tasks.accounting_measure_compute import (
    compile_measures,
    get_exercice_dates_from_date,
)
from caerp.models.accounting.operations import (
    AccountingOperation,
    AccountingOperationUpload,
)
from caerp.models.base import DBSESSION
from caerp.models.company import Company
from caerp.utils.accounting import get_cae_accounting_software
from caerp.utils.mail import send_mail

logger = utils.get_logger(__name__)
FILENAME_ERROR = (
    "Le fichier ne respecte pas la nomenclature de nom attendue (ex : "
    "2017_12_resultat.slk)",
)

MAIL_ERROR_SUBJECT = "[ERREUR] Traitement de votre document \
{filename}"

MAIL_ERROR_BODY = """Une erreur est survenue lors du traitement du
fichier {filename}:

    {error}
"""
MAIL_UNKNOWN_ERROR_BODY = """Une erreur inconnue est survenue lors du
traitement du fichier {filename}:

    {error}

Veuillez contacter votre administrateur
"""
MAIL_SUCCESS_SUBJECT = """[Succès] Traitement de votre document {0}"""
MAIL_SUCCESS_BODY = """Le fichier {0} a été traité avec succès.
Écritures générées : {1}
Écritures n'ayant pas pu être associées à une entreprise existante : {2}

Les indicateurs ont été générés depuis ces écritures.
"""


def _get_base_path() -> Path:
    """
    Retreive the base working path as configured in the ini file
    """
    return Path(get_setting("caerp.parsing_pool_parent", mandatory=True))


def _get_path(directory) -> Path:
    """
    Return the abs path for the given directory

    :param str directory: The directory name pool/error/processed
    :rtype: str
    """
    return _get_base_path().joinpath(directory)


def _get_file_path_from_pool(pool_path: Path) -> Optional[Path]:
    """
    Handle file remaining in the pool

    :param pool_path: The pool path to look into
    :returns: The Path of the first file we find in the rep
    :rtype: str
    """
    result = None
    if pool_path.is_dir():
        for path in pool_path.iterdir():
            if path.is_file():
                result = path
                break
    return result


def _mv_file(file_path: Path, queue: str = "processed"):
    """
    Move the file to the processed directory
    """
    if file_path.is_file():
        new_dir = _get_path(queue)
        new_file_path = os.path.join(new_dir, file_path.name)
        os.system('mv "{0}" "{1}"'.format(file_path, new_file_path))
        logger.info(
            "The file {0} has been moved to the {1} directory".format(
                file_path,
                new_dir,
            )
        )
        return new_file_path
    else:
        raise Exception("File is missing {}".format(file_path))


def _clean_old_operations(old_ids, date_ref=None):
    """
    Clean old AccountingOperation entries

    :param list old_ids: The ids of items to remove
    :param date date_ref: The date from where we remove the items
    """
    op = AccountingOperation.__table__.delete().where(
        AccountingOperation.id.in_(old_ids)
    )
    if date_ref:
        op = op.where(AccountingOperation.date >= date_ref)
    op.execute()


class AccountingDataHandler:
    """
    Accounting datas parser : parses a General Ledger file
    """

    def __init__(self, parser: BaseParser, producer: BaseProducer, force: bool = False):
        self.parser = parser
        self.producer = producer
        self.force = force
        self.company_id_cache = {}

    def _load_company_id_cache(self):
        """
        Load company ids in a cache to avoid looking for them with each operation we
        treat
        """
        query = (
            DBSESSION()
            .query(distinct(Company.code_compta))
            .filter(Company.code_compta != None)  # noqa: E711
        )
        for (code_compta,) in query:
            company_id = Company.get_id_by_analytical_account(code_compta)
            self.company_id_cache[code_compta] = company_id

    def _find_company_id(self, analytical_account: str) -> Optional[int]:
        """
        Find a company object starting from its analytical_account

        :param str analytical_account: The account
        :returns: The company's id
        """
        return self.company_id_cache.get(analytical_account)

    def _build_operation_upload_object(self) -> AccountingOperationUpload:
        """
        Build an AccountingOperationUpload instance with current file datas

        :returns: An AccountingOperationUpload for the current parsed file
        """
        upload_data: UploadMetaData = self.parser.metadata()
        return AccountingOperationUpload(**upload_data.__dict__)

    def _get_existing_operation_ids(self) -> List[int]:
        """
        Return ids of the operations already stored in database
        """
        return [entry[0] for entry in DBSESSION().query(AccountingOperation.id)]

    def _get_upload_infos_from_operations_stream(
        self, exercice_start_date
    ) -> tuple[Optional[datetime.date], Optional[datetime.date], bool]:
        """
        Return needed informations from streamed operations

        :returns date first_date: date of the first operation in chronological order
        :returns bool is_previous_closure_done: if we can consider that previous fiscal
        year has been closed or not, based on existance of 6 or 7 operations before
        actual fiscal year start
        """
        first_date = None
        is_previous_closure_done = True
        last_date = None
        today = datetime.date.today()
        for operation in self.producer.stream_operations():
            if first_date is None or operation.date < first_date:
                first_date = operation.date

            if last_date is None or operation.date > last_date:
                last_date = min(operation.date, today)
            if (
                operation.general_account[:1] in ("6", "7")
                and operation.date < exercice_start_date
            ):
                is_previous_closure_done = False
        return first_date, last_date, is_previous_closure_done

    def run(self) -> Tuple[int, int, List[int], Optional[datetime.date]]:
        self._load_company_id_cache()
        upload = self._build_operation_upload_object()
        old_ids = self._get_existing_operation_ids()
        (exercice_start, exercice_end) = get_exercice_dates_from_date(upload.date)
        previous_exercice_start = exercice_start - relativedelta(years=1)
        (
            first_operation_date,
            last_operation_date,
            closure_done,
        ) = self._get_upload_infos_from_operations_stream(exercice_start)
        upload.date = last_operation_date
        cae_accounting_software = get_cae_accounting_software()[0]
        missed_operations: int = 0
        operations = []
        for operation_data in self.producer.stream_operations():
            if cae_accounting_software == "quadra":
                if closure_done and operation_data.date < exercice_start:
                    operation_data.date = exercice_start
                elif operation_data.date < previous_exercice_start:
                    operation_data.date = previous_exercice_start
            company_id = self._find_company_id(operation_data.analytical_account)
            if not company_id:
                missed_operations += 1
            operations.append(
                AccountingOperation(company_id=company_id, **operation_data.__dict__)
            )
        if operations:
            logger.info(f"    {len(operations)} operations")
            upload.operations = operations
        else:
            logger.info(f"    no operation found")
            old_ids = []

        if upload.id:
            upload = DBSESSION().merge(upload)
        else:
            DBSESSION().add(upload)
        DBSESSION().flush()

        return upload.id, missed_operations, old_ids, first_operation_date


def send_error(request, mail_addresses, filename, err):
    """
    Send an error email to mail_addresses
    """
    if mail_addresses:
        try:
            error = getattr(err, "message", str(err))
            message = MAIL_ERROR_BODY.format(error=error, filename=filename)
            subject = MAIL_ERROR_SUBJECT.format(filename=filename)
            send_mail(
                request,
                mail_addresses,
                message,
                subject,
            )
        except Exception:
            logger.exception("send_success error")


def send_unknown_error(request, mail_addresses, filename, err):
    if mail_addresses:
        try:
            subject = MAIL_ERROR_SUBJECT.format(filename=filename)

            message = MAIL_UNKNOWN_ERROR_BODY.format(error=str(err), filename=filename)
            send_mail(
                request,
                mail_addresses,
                message,
                subject,
            )
        except Exception:
            logger.exception("send_success error")


def send_success(request, mail_addresses, filename, new_entries, missing):
    if mail_addresses:
        try:
            subject = MAIL_SUCCESS_SUBJECT.format(filename)
            message = MAIL_SUCCESS_BODY.format(
                filename,
                new_entries,
                missing,
            )
            send_mail(
                request,
                mail_addresses,
                message,
                subject,
            )
        except Exception:
            logger.exception("send_success error")


def _move_file_to_processing(waiting_file: Path):
    """
    MOve the waiting file to the processing queue

    :param waiting_file: The full path to the file to process
    """
    logger.info(" + Moving the file to the processing directory")
    file_to_parse = _mv_file(waiting_file, "processing")
    return file_to_parse


def _is_processing() -> bool:
    """
    Check if there is already a parsing process running
    """
    path = _get_path("processing")

    for filepath in path.iterdir():
        if filepath.is_file():
            return True
    return False


def _prepare_file() -> Optional[Path]:
    """
    Return the path to a file that should be treated (or None if None should be treated)
    """
    pool_path = _get_path("pool")
    waiting_file = _get_file_path_from_pool(pool_path)

    if waiting_file is None:
        return

    already_processing = _is_processing()

    if already_processing:
        logger.info("A parsing is already processing")
        return

    else:
        file_to_parse = _move_file_to_processing(waiting_file)
        logger.info("Parsing an accounting file : %s" % file_to_parse)
        return Path(file_to_parse)


def _get_file_parser(request, file_path: Path) -> BaseParser:
    """
    Return the parser to be used when handling this file
    """
    factory = request.find_service_factory(IAccountingFileParser)
    return factory(file_path, request)


def _get_operation_producer(request, parser: BaseParser) -> BaseProducer:
    """
    Build the tool that produces OperationData
    """
    factory = request.find_service_factory(IAccountingOperationProducer)
    return factory(parser, request)


@celery_app.task(bind=True)
def handle_pool_task(self, force=False):
    """
    Parse the files present in the configured file pool
    """
    # Préparation du fichier à traiter
    file_path = _prepare_file()
    if file_path is None:
        return

    request = get_request()
    mail_addresses = get_recipients_addresses(request)
    try:
        parser = _get_file_parser(request, file_path)
        producer = _get_operation_producer(request, parser)
        handler = AccountingDataHandler(parser, producer, force=force)
        transaction.begin()
        logger.info("  + Storing accounting operations in database")
        (
            upload_object_id,
            missed_associations,
            old_ids,
            first_upload_date,
        ) = handler.run()
        logger.debug("  + File was processed")
        transaction.commit()

    except FileNameException as exc:
        transaction.abort()
        logger.exception("Filename is incorrect")
        logger.exception("* FAILED : transaction has been rollbacked")
        if mail_addresses:
            send_error(request, mail_addresses, file_path.name, exc)
            logger.error("An error mail has been sent to {0}".format(mail_addresses))
        _mv_file(file_path, "error")
        return False

    except Exception as err:
        transaction.abort()
        logger.exception("Unkown Error")
        logger.exception("* FAILED : transaction has been rollbacked")
        if mail_addresses:
            send_unknown_error(request, mail_addresses, file_path.name, err)
            logger.error("An error mail has been sent to {0}".format(mail_addresses))
        _mv_file(file_path, "error")
        logger.error("File has been moved to error directory")
        return False

    else:
        logger.info("Accounting operations where successfully stored")
        _mv_file(file_path)
        logger.info("File has been moved to processed directory")

    if old_ids:
        transaction.begin()
        logger.info("  + Cleaning old operations")
        try:
            _clean_old_operations(old_ids, first_upload_date)
            transaction.commit()
        except Exception:
            transaction.abort()
            logger.exception("Error while cleaning old operations")
        else:
            logger.info(" * Old datas cleaned successfully")

    if upload_object_id:
        compile_measures(upload_object_id)

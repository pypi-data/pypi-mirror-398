"""
Celery tasks used to asynchronously generate exports (like excel exports)


Workflow :
    user provide filters
    TODO : user provide columns

    For UserDatas exports, we need to add some fields


    1- Task entry
    2- retrieve model
    3- generate the file or re-use the cached one
"""
import json
import os
from tempfile import mktemp

import transaction
from beaker.cache import cache_region
from celery.utils.log import get_task_logger
from dateutil.utils import today
from pyramid_celery import celery_app
from sqla_inspect.csv import CsvExporter, SqlaCsvExporter
from sqla_inspect.excel import SqlaXlsExporter, XlsExporter
from sqla_inspect.ods import OdsExporter, SqlaOdsExporter
from sqlalchemy import desc, func
from sqlalchemy.orm import RelationshipProperty
from sqlalchemy.sql.expression import label

from caerp.celery.conf import get_request, get_setting
from caerp.celery.models import FileGenerationJob
from caerp.celery.tasks import utils
from caerp.compute.math_utils import integer_to_amount, round
from caerp.export.sale_product import serialize_catalog
from caerp.export.utils import format_filename
from caerp.models.company import Company
from caerp.models.expense import ExpenseSheet
from caerp.models.task import Task
from caerp.utils.datetimes import format_date
from caerp.utils.html import strip_html_tags

MODELS_CONFIGURATION = {}

logger = utils.get_logger(__name__)


GENERATION_ERROR_MESSAGE = (
    "Une erreur inconnue a été rencontrée à la génération de votre fichier, "
    "veuillez contacter votre administrateur en lui "
    "fournissant l'identifiant suivant : %s"
)


def _add_o2m_headers_to_writer(writer, query, id_key):
    """
    Add column headers in the form "label 1",  "label 2" ... to be able to
    insert the o2m related elements to a main model's table export (allow to
    have 3 dimensionnal datas in a 2d array)

    E.g : Userdatas objects have got a o2m relationship on DateDatas objects

    Here we would add date 1, date 2... columns regarding the max number of
    configured datas (if a userdatas has 5 dates, we will have 5 columns)
    We fill the column with the value of an attribute of the DateDatas model
    (that is handled by sqla_inspect thanks to the couple index + related_key
    configuration)

    The name of the attribute is configured using the "flatten" key in the
    relationship's export configuration

    :param str id_key: The foreign key attribute mostly matching the class we
    export (e.g : when exporting UserDatas, most of the related elements point
    to it through a userdatas_id foreign key)
    """
    from caerp.models.base import DBSESSION

    new_headers = []
    for header in writer.headers:
        if isinstance(header["__col__"], RelationshipProperty):
            if header["__col__"].uselist:
                class_ = header["__col__"].mapper.class_
                # On compte le nombre maximum d'objet lié que l'on rencontre
                # dans la base
                if not hasattr(class_, id_key):
                    continue

                count = (
                    DBSESSION()
                    .query(label("nb", func.count(class_.id)))
                    .group_by(getattr(class_, id_key))
                    .order_by(desc("nb"))
                    .first()
                )

                if count is not None:
                    count = count[0]
                else:
                    count = 0

                # Pour les relations O2M qui ont un attribut flatten de
                # configuré, On rajoute des colonnes "date 1" "date 2" dans
                # notre sheet principale
                for index in range(0, count):
                    if "flatten" in header:
                        flatten_keys = header["flatten"]
                        if not hasattr(flatten_keys, "__iter__"):
                            flatten_keys = [flatten_keys]

                        for flatten_key, flatten_label in flatten_keys:
                            new_header = {
                                "__col__": header["__col__"],
                                "label": "%s %s %s"
                                % (header["label"], flatten_label, index + 1),
                                "key": header["key"],
                                "name": "%s_%s_%s"
                                % (header["name"], flatten_key, index + 1),
                                "related_key": flatten_key,
                                "index": index,
                            }
                            new_headers.append(new_header)

    writer.headers.extend(new_headers)
    return writer


def _get_tmp_directory_path():
    """
    Return the tmp filepath configured in the current configuration
    :param obj request: The pyramid request object
    """
    asset_path_spec = get_setting("caerp.static_tmp", mandatory=True)
    return asset_path_spec


def _get_tmp_filepath(directory, basename, extension):
    """
    Return a temp filepath for the given filename

    :param str basename: The base name to use
    :returns: A path to a non existing file
    :rtype: str
    """
    if not extension.startswith("."):
        extension = "." + extension

    filepath = mktemp(prefix=basename, suffix=extension, dir=directory)
    while os.path.exists(filepath):
        filepath = mktemp(prefix=basename, suffix=extension, dir=directory)
    return filepath


def _get_open_file(filepath, extension):
    """
    Get the appropriate writing mode regarding the provided extension
    """
    if extension in ("csv", "json"):
        return open(filepath, "w", newline="")
    else:
        return open(filepath, "wb")


def _transform_list_header_in_export_header(list_header, col_prefix="col_"):
    """
    Transform header formated in list of lists
    (eg: ['aaa', 'bbb', 'ccc'])
    into an exportable list of dicts
    (eg: [
            {"label": "aaa", "name": "col_1"},
            {"label": "bbb", "name": "col_2"},
            {"label": "ccc", "name": "col_3"},
        ]
    )
    """
    col_num = 1
    export_header = []
    for header in list_header:
        export_header.append(
            {
                "label": header,
                "name": f"{col_prefix}{col_num}",
            }
        )
        col_num += 1
    return export_header


def _transform_list_data_in_export_data(list_data, col_prefix="col_"):
    """
    Transform data formated in list of lists
    (eg: [['aaa', 'bbb', 'ccc'], ['ddd', 'eee', 'fff']])
    into an exportable list of dicts
    (eg: [
            {"col_1": "aaa", "col_2": "bbb", "col_3": "ccc"},
            {"col_1": "ddd", "col_2": "eee", "col_3": "fff"},
        ]
    )
    """
    export_data = []
    if len(list_data) > 0:
        col_num = 1
        col_list = []
        while col_num <= len(list_data[0]):
            col_list.append(f"{col_prefix}{col_num}")
            col_num += 1
        for row in list_data:
            export_data.append(dict(zip(col_list, row)))
    return export_data


@cache_region("default_term")
def _write_file_on_disk(tmpdir, model_type, ids, filename, extension):
    """
    Return a path to a generated file

    :param str tmpdir: The path to write to
    :param str model_type: The model key we want to generate an ods file for
    :param list ids: An iterable containing all ids of models to be included in
    the output
    :param str filename: The path to the file output
    :param str extension: The desired extension (xls/ods)
    :returns: The name of the generated file (unique and temporary name)
    :rtype: str
    """
    logger.debug(" No file was cached yet")
    config = MODELS_CONFIGURATION[model_type]
    model = config["factory"]
    query = model.query()
    if ids is not None:
        query = query.filter(model.id.in_(ids))

    options = {}
    if "excludes" in config:
        options["excludes"] = config["excludes"]
    if "order" in config:
        options["order"] = config["order"]
    if extension == "ods":
        writer = SqlaOdsExporter(model=model, **options)
    elif extension in ("xls", "xlsx"):
        writer = SqlaXlsExporter(model=model, **options)
    elif extension == "csv":
        writer = SqlaCsvExporter(model=model, **options)

    writer = _add_o2m_headers_to_writer(writer, query, config["foreign_key_name"])

    if "hook_init" in config:
        writer = config["hook_init"](writer, query)

    for item in query:
        writer.add_row(item)
        if "hook_add_row" in config:
            config["hook_add_row"](writer, item)

    filepath = _get_tmp_filepath(tmpdir, filename, extension)
    logger.debug(" + Writing file to %s" % filepath)

    # Since csv module expects strings
    with _get_open_file(filepath, extension) as f_buf:
        writer.render(f_buf)
    return os.path.basename(filepath)


@celery_app.task(bind=True)
def export_to_file(self, job_id, model_type, ids, filename="test", file_format="ods"):
    """
    Export the datas provided in the given query to ods format and generate a

    :param int job_id: The id of the job object used to record file_generation
    informations
    :param str model_type: The model we want to export (see MODELS)
    :param list ids: List of ids to query
    :param str filename: The base filename to use for the export (unique string
    is appended)
    :param str file_format: The format in which we want to export
    """
    logger = get_task_logger(__name__)
    logger.info("Exporting to a file")
    logger.info(" + model_type : %s", model_type)
    logger.info(" + ids : %s", ids)

    # Mark job started
    utils.start_job(self.request, FileGenerationJob, job_id)

    filename = format_filename(filename)

    # Execute actions
    try:
        tmpdir = _get_tmp_directory_path()
        result_filename = _write_file_on_disk(
            tmpdir,
            model_type,
            ids,
            filename,
            file_format,
        )
        logger.debug(" -> The file %s been written", result_filename)
        transaction.commit()
    except Exception:
        transaction.abort()
        logger.exception("Error while generating file")
        errors = [GENERATION_ERROR_MESSAGE % job_id]
        utils.record_failure(FileGenerationJob, job_id, errors)
    else:
        utils.record_completed(FileGenerationJob, job_id, filename=result_filename)

    return ""


def _export_data_to_tabular_file(headers, data, filename="export", file_format="csv"):
    """
    Generic function to export given data to given format

    :param list headers: List of dicts with headers data, format :
        (
            {"label": "Column label", "name": "col_1"},
            {"label": "Column label 2", "name": "col_2"},
        )
    :param list data: List of dicts with rows data for each headers, format :
        (
            {"col_1": "Value row 1 col 1", "col_2": "Value row 1 col 2"},
            {"col_1": "Value row 2 col 1", "col_2": "Value row 2 col 2"},
        )
    :param str filename: The base filename to use for the export
    :param str file_format: The format in which we want to export
    """
    logger = get_task_logger(__name__)
    logger.info("    + Exporting data to file")

    tmpdir = _get_tmp_directory_path()
    filename = format_filename(filename)
    if file_format == "ods":
        writer = OdsExporter()
    elif file_format == "xls":
        writer = XlsExporter()
    else:
        writer = CsvExporter()

    writer.headers = headers
    writer.set_datas(data)

    filepath = _get_tmp_filepath(tmpdir, filename, file_format)
    logger.debug(" + Writing file to %s" % filepath)
    with _get_open_file(filepath, file_format) as f_buf:
        writer.render(f_buf)
    result_filename = os.path.basename(filepath)

    logger.debug(f" -> The file {result_filename} been written")
    return result_filename


def amount_to_export_str(amount: int, precision: int = 5) -> str:
    """
    Convert amounts (as integers) in an exportable string
    """
    return round(integer_to_amount(amount, precision=precision, default=0), 2)


@celery_app.task(bind=True)
@cache_region("default_term", "estimations_details")
def export_estimations_details_to_file(self, job_id, task_ids, format="csv"):
    """
    Exporting details (each lines) of given estimations

    :param int job_id: The id of the job object
    :param list task_ids: List of estimations ids to query
    :param str format: The format in which we want to export
    """

    logger.info(
        f" + Exporting details for the following estimations's ids : {task_ids}"
    )

    # Mark job started
    utils.start_job(self.request, FileGenerationJob, job_id)

    headers = (
        {"label": "Enseigne", "name": "company"},
        {"label": "N°Devis", "name": "estimation_number"},
        {"label": "Date", "name": "estimation_date"},
        {"label": "Client", "name": "customer"},
        {"label": "Description", "name": "description"},
        {"label": "Prix Unit. HT", "name": "unit_ht"},
        {"label": "Prix Unit. TTC", "name": "unit_ttc"},
        {"label": "Quantité", "name": "quantity"},
        {"label": "Unité", "name": "unity"},
        {"label": "TVA", "name": "tva"},
        {"label": "Total HT", "name": "total_ht"},
        {"label": "Total TVA", "name": "tva_amount"},
        {"label": "Total TTC", "name": "total_ttc"},
        {"label": "Compte produit", "name": "product"},
    )

    try:
        data = []
        query = (
            Task.query().filter(Task.id.in_(task_ids)).order_by(Task.status_date.desc())
        )
        for estimation in query:
            estimation_product = None
            logger.debug(f" + Collecting data for estimation {estimation.id}")
            for line in estimation.all_lines:
                logger.debug(f"    > Computing data for line {line.id}")
                line_product = line.product.name if line.product else ""
                row_data = {
                    "company": estimation.company.name,
                    "estimation_number": estimation.internal_number,
                    "estimation_date": format_date(estimation.date),
                    "customer": estimation.customer.label,
                    "description": strip_html_tags(line.description),
                    "unit_ht": amount_to_export_str(line.unit_ht()),
                    "unit_ttc": amount_to_export_str(line.unit_ttc()),
                    "quantity": line.quantity,
                    "unity": line.unity,
                    "tva": amount_to_export_str(max(line.tva.amount, 0), 4),
                    "total_ht": amount_to_export_str(line.total_ht()),
                    "tva_amount": amount_to_export_str(line.tva_amount()),
                    "total_ttc": amount_to_export_str(line.total()),
                    "product": line_product,
                }
                data.append(row_data)
                if estimation_product is None:
                    estimation_product = line_product
                elif line_product != estimation_product:
                    estimation_product = ""
            for discount in estimation.discounts:
                logger.debug(f"    > Computing data for discount {discount.id}")
                row_data = {
                    "company": estimation.company.name,
                    "estimation_number": estimation.internal_number,
                    "estimation_date": format_date(estimation.date),
                    "customer": estimation.customer.label,
                    "description": strip_html_tags(discount.description),
                    "unit_ht": amount_to_export_str(discount.total_ht() * -1),
                    "unit_ttc": amount_to_export_str(discount.total() * -1),
                    "quantity": 1,
                    "unity": "remise",
                    "tva": amount_to_export_str(max(discount.tva.amount, 0), 4),
                    "total_ht": amount_to_export_str(discount.total_ht() * -1),
                    "tva_amount": amount_to_export_str(discount.tva_amount() * -1),
                    "total_ttc": amount_to_export_str(discount.total() * -1),
                    "product": estimation_product,
                    "date": "",
                }
                data.append(row_data)
        logger.info(" + All estimations's details data where collected !")

        result_filename = _export_data_to_tabular_file(
            headers, data, filename="detail_devis_", file_format=format
        )
    except Exception:
        logger.exception("Error while generating export file")
        errors = [GENERATION_ERROR_MESSAGE % job_id]
        utils.record_failure(FileGenerationJob, job_id, errors)
    else:
        utils.record_completed(FileGenerationJob, job_id, filename=result_filename)
    return ""


@celery_app.task(bind=True)
@cache_region("default_term", "invoices_details")
def export_invoices_details_to_file(self, job_id, task_ids, format="csv"):
    """
    Exporting details (each lines) of given invoices

    :param int job_id: The id of the job object
    :param list task_ids: List of invoices ids to query
    :param str format: The format in which we want to export
    """

    logger.info(f" + Exporting details for the following invoice's ids : {task_ids}")

    # Mark job started
    utils.start_job(self.request, FileGenerationJob, job_id)

    headers = (
        {"label": "Enseigne", "name": "company"},
        {"label": "Facture", "name": "invoice_number"},
        {"label": "Date", "name": "invoice_date"},
        {"label": "Client", "name": "customer"},
        {"label": "Description", "name": "description"},
        {"label": "Prix Unit. HT", "name": "unit_ht"},
        {"label": "Prix Unit. TTC", "name": "unit_ttc"},
        {"label": "Quantité", "name": "quantity"},
        {"label": "Unité", "name": "unity"},
        {"label": "TVA", "name": "tva"},
        {"label": "Total HT", "name": "total_ht"},
        {"label": "Total TVA", "name": "tva_amount"},
        {"label": "Total TTC", "name": "total_ttc"},
        {"label": "Compte produit", "name": "product"},
        {"label": "Date d'exécution", "name": "date"},
    )

    try:
        data = []
        query = (
            Task.query().filter(Task.id.in_(task_ids)).order_by(Task.status_date.desc())
        )
        for invoice in query:
            invoice_product = None
            logger.debug(f" + Collecting data for invoice {invoice.id}")
            for line in invoice.all_lines:
                logger.debug(f"    > Computing data for line {line.id}")
                line_product = line.product.name if line.product else ""
                row_data = {
                    "company": invoice.company.name,
                    "invoice_number": invoice.official_number,
                    "invoice_date": format_date(invoice.date),
                    "customer": invoice.customer.label,
                    "description": strip_html_tags(line.description),
                    "unit_ht": amount_to_export_str(line.unit_ht()),
                    "unit_ttc": amount_to_export_str(line.unit_ttc()),
                    "quantity": line.quantity,
                    "unity": line.unity,
                    "tva": amount_to_export_str(max(line.tva.amount, 0), 4),
                    "total_ht": amount_to_export_str(line.total_ht()),
                    "tva_amount": amount_to_export_str(line.tva_amount()),
                    "total_ttc": amount_to_export_str(line.total()),
                    "product": line_product,
                    "date": format_date(line.date),
                }
                data.append(row_data)
                if invoice_product is None:
                    invoice_product = line_product
                elif line_product != invoice_product:
                    invoice_product = ""
            for discount in invoice.discounts:
                logger.debug(f"    > Computing data for discount {discount.id}")
                row_data = {
                    "company": invoice.company.name,
                    "invoice_number": invoice.official_number,
                    "invoice_date": format_date(invoice.date),
                    "customer": invoice.customer.label,
                    "description": strip_html_tags(discount.description),
                    "unit_ht": amount_to_export_str(discount.total_ht() * -1),
                    "unit_ttc": amount_to_export_str(discount.total() * -1),
                    "quantity": 1,
                    "unity": "remise",
                    "tva": amount_to_export_str(max(discount.tva.amount, 0), 4),
                    "total_ht": amount_to_export_str(discount.total_ht() * -1),
                    "tva_amount": amount_to_export_str(discount.tva_amount() * -1),
                    "total_ttc": amount_to_export_str(discount.total() * -1),
                    "product": invoice_product,
                    "date": "",
                }
                data.append(row_data)
        logger.info(" + All invoice's details data where collected !")

        result_filename = _export_data_to_tabular_file(
            headers, data, filename="detail_factures_", file_format=format
        )
    except Exception:
        logger.exception("Error while generating export file")
        errors = [GENERATION_ERROR_MESSAGE % job_id]
        utils.record_failure(FileGenerationJob, job_id, errors)
    else:
        utils.record_completed(FileGenerationJob, job_id, filename=result_filename)
    return ""


@celery_app.task(bind=True)
@cache_region("default_term", "expenses")
def export_expenses_to_file(self, job_id, expense_ids, filename, format="csv"):
    """
    export expenses to file

    :param int job_id: The id of the job object
    :param list expense_ids: List of expenses ids to query
    :param str format: The format in which we want to export
    """

    logger.debug(
        f" + Exporting details for the following expenses's ids : {expense_ids}"
    )

    # Mark job started
    utils.start_job(self.request, FileGenerationJob, job_id)

    headers = (
        {"label": "Numéro de pièce", "name": "official_number"},
        {"label": "Titre", "name": "title"},
        {"label": "Entrepreneur", "name": "user_name"},
        {"label": "Enseigne", "name": "company_name"},
        {"label": "Année", "name": "year"},
        {"label": "Mois", "name": "month"},
        {"label": "HT", "name": "ht"},
        {"label": "TVA", "name": "tva"},
        {"label": "TTC", "name": "ttc"},
        {"label": "Km", "name": "km"},
        {"label": "Justificatifs reçus et acceptés", "name": "justified"},
        {"label": "Paiements", "name": "paid"},
        {"label": "Montant restant dû", "name": "topay"},
    )

    expense_justified_status = {
        0: "non",
        1: "oui",
    }
    expense_paid_status = {
        "resulted": "intégral",
        "paid": "partiel",
        "waiting": "en attente",
    }

    try:
        data = []
        query = ExpenseSheet.query().filter(ExpenseSheet.id.in_(expense_ids))
        for expense in query:
            # compute topay column
            topay = 0
            if hasattr(expense, "topay") and not expense.paid_status == "resulted":
                topay = integer_to_amount(expense.topay())

            row_data = {
                "official_number": expense.official_number,
                "title": expense.title,
                "user_name": expense.user.label,
                "company_name": expense.company.name,
                "year": expense.year,
                "month": expense.month,
                "ht": integer_to_amount(expense.total_ht),
                "tva": integer_to_amount(expense.total_tva),
                "ttc": integer_to_amount(expense.total),
                "km": integer_to_amount(expense.total_km),
                "justified": expense_justified_status.get(
                    expense.justified, expense.justified
                ),
                "paid": expense_paid_status.get(
                    expense.paid_status, expense.paid_status
                ),
                "topay": topay,
            }
            data.append(row_data)
        result_filename = _export_data_to_tabular_file(
            headers, data, filename=filename, file_format=format
        )
    except Exception:
        logger.exception("Error while generating export file")
        errors = [GENERATION_ERROR_MESSAGE % job_id]
        utils.record_failure(FileGenerationJob, job_id, errors)
    else:
        utils.record_completed(FileGenerationJob, job_id, filename=result_filename)
    return ""


@celery_app.task(bind=True)
def export_dataquery_to_file(
    self, job_id, dataquery_name, format="csv", start=None, end=None
):
    """
    Exporting the result of the given dataquery in a file with the given format

    :param int job_id: Id of the job object
    :param list dataquery_name: Name of the dataquery we want
    :param str format: The format in which we want to export
    :param str start: The start date of the query (if needed)
    :param str end: The end date of the query (if needed)
    """

    logger.debug(f" + Exporting results of dataquery : {dataquery_name}")

    # Mark job started
    utils.start_job(self.request, FileGenerationJob, job_id)

    # Import and create the dataquery object from caerp
    try:
        pyramid_request = get_request()
        dataquery_object = pyramid_request.get_dataquery(dataquery_name)
        dataquery_object.set_dates(start, end)
    except Exception:
        logger.error(f"ABORT : Unable to instanciate dataquery '{dataquery_name}'")
        errors = [GENERATION_ERROR_MESSAGE % job_id]
        utils.record_failure(FileGenerationJob, job_id, errors)
        return ""

    # Generating dataquery headers and data
    headers = _transform_list_header_in_export_header(dataquery_object.headers())
    data = _transform_list_data_in_export_data(dataquery_object.data())
    logger.info(" + Query data collected !")

    # Exporting dataquery result in a file
    try:
        datequery_filename = f"{dataquery_object.name}_"
        if dataquery_object.start_date:
            datequery_filename += f"{dataquery_object.start_date.strftime('%Y-%m-%d')}_"
        if dataquery_object.end_date:
            datequery_filename += f"{dataquery_object.end_date.strftime('%Y-%m-%d')}_"
        result_filename = _export_data_to_tabular_file(
            headers, data, filename=datequery_filename, file_format=format
        )
    except Exception:
        logger.exception("Error while generating dataquery export file")
        errors = [GENERATION_ERROR_MESSAGE % job_id]
        utils.record_failure(FileGenerationJob, job_id, errors)
    else:
        utils.record_completed(FileGenerationJob, job_id, filename=result_filename)
    return ""


@celery_app.task(bind=True)
def export_company_sales_catalog_to_json(
    self,
    job_id,
    company_id,
):
    """
    Exports a sales catalog from a company to a JSON file

    Sales catalog is a complex nested data structure, thus tabular data is not appropriate for it.
    """

    logger = get_task_logger(__name__)

    logger.info(f" + Exporting sales catalog for company : {company_id}")

    # Mark job started
    utils.start_job(self.request, FileGenerationJob, job_id)

    try:
        company = Company.get(company_id)
        filename = format_filename(f"{today():%Y-%m-%d} export-catalog-{company.name}")
        file_extension = "json"

        tmpdir = _get_tmp_directory_path()

        filepath = _get_tmp_filepath(tmpdir, filename, file_extension)

        data = serialize_catalog(company)

        logger.debug(" + Writing file to %s" % filepath)

        with _get_open_file(filepath, file_extension) as f_buf:
            f_buf.write(json.dumps(data, indent=2))

        result_filename = os.path.basename(filepath)

    except Exception:
        logger.exception("Error while generating file")
        errors = [GENERATION_ERROR_MESSAGE % job_id]
        utils.record_failure(FileGenerationJob, job_id, errors)

    else:
        logger.debug(f" -> The file {result_filename} been written")
        utils.record_completed(FileGenerationJob, job_id, filename=result_filename)

        return result_filename

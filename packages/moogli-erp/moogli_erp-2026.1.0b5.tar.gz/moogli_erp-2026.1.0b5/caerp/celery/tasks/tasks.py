import transaction

from caerp.celery.conf import get_request
from caerp.celery.hacks import setup_rendering_hacks
from caerp.celery.mail import (
    send_customer_new_invoice_mail,
    send_customer_new_order_mail,
    send_supplier_new_invoice_mail,
    send_supplier_new_order_mail,
)
from caerp.celery.tasks import utils
from caerp.celery.transactional_task import task_tm
from caerp.export.task_pdf import ensure_task_pdf_persisted

logger = utils.get_logger(__name__)


def _get_task_from_id(task_id):
    document = utils.get_task(task_id)
    if document is None:
        raise Exception(f"Document with id {task_id} doesn't exist in database")
    return document


@task_tm
def scheduled_render_pdf_task(document_id):
    logger.debug("Scheduling a PDF render Task for {}".format(document_id))
    document = _get_task_from_id(document_id)
    request = get_request()
    try:
        setup_rendering_hacks(request, document)
        utils.set_current_user(request, document.status_user_id)
        ensure_task_pdf_persisted(document, request)
        transaction.commit()
    except Exception:
        logger.exception("Error in scheduled_render_pdf_task")
        transaction.abort()


@task_tm
def async_internalestimation_valid_callback(document_id):
    """
    Handle the transfer of an InternalEstimation to the Client Company

    - Ensure supplier exists
    - Generates the PDF
    - Create a Supplier Order and attache the pdf file
    """
    logger.debug(f"Async internal estimation validation callback for {document_id}")
    document = _get_task_from_id(document_id)
    request = get_request()
    try:
        logger.debug("Setup rendering hacks")
        setup_rendering_hacks(request, document)
        utils.set_current_user(request, document.status_user_id)
        order = document.sync_with_customer(request)
        send_customer_new_order_mail(request, order)
        send_supplier_new_order_mail(request, order)
        transaction.commit()
    except Exception:
        logger.exception("Error in async_internalestimation_valid_callback")
        transaction.abort()


@task_tm
def async_internalinvoice_valid_callback(document_id):
    """
    Handle the transfer of an InternalInvoice to the Client Company

    - Ensure supplier exists
    - Generates the PDF
    - Create a Supplier Invoice and attach the pdf file
    """
    logger.debug(f"Async internal invoice validation callback for {document_id}")
    document = _get_task_from_id(document_id)
    request = get_request()
    try:
        setup_rendering_hacks(request, document)
        utils.set_current_user(request, document.status_user_id)
        supplier_invoice = document.sync_with_customer(request)
        send_customer_new_invoice_mail(request, supplier_invoice)
        send_supplier_new_invoice_mail(request, supplier_invoice)
        transaction.commit()
    except Exception:
        logger.exception("Error in async_internalinvoice_valid_callback")
        transaction.abort()

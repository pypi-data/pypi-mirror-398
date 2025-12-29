from typing import List

from caerp.controllers.files import copy_files_from_node
from caerp.controllers.task.task import (
    get_task_params_from_other_task,
    task_on_before_commit,
)
from caerp.models.task import Estimation, Invoice
from caerp.models.task.services.invoice import InvoiceService
from caerp.services.business import guess_payment_deadline_from_invoice


def attach_invoice_to_estimation(request, invoice: Invoice, estimation: Estimation):
    """Attach an invoice to an estimation and handle business related informations"""
    estimation.geninv = True
    invoice.estimation_id = estimation.id
    business = estimation.business
    copy_files_from_node(request, invoice.business, business)
    invoice.business_id = business.id
    guess_payment_deadline_from_invoice(request, business, invoice)
    business.status_service.update_invoicing_status(business, invoice)
    # On supprime l'affaire si nécessaire
    task_on_before_commit(request, invoice, "delete")

    request.dbsession.merge(estimation)
    request.dbsession.merge(invoice)


def attach_invoices_to_estimation(
    request, estimation: Estimation, invoices: List[Invoice] = None
):
    for invoice in invoices:
        attach_invoice_to_estimation(request, invoice, estimation)


def gen_common_invoice_from_invoice(request, user, invoice: Invoice) -> Invoice:
    """
    Create a similar invoice into the same business context
    """
    params = get_task_params_from_other_task(request, user, invoice)
    invoice = InvoiceService.create(request, invoice.customer, params)
    return invoice

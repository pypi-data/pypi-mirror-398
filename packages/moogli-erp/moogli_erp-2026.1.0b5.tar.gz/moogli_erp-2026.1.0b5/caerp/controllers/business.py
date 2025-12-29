from typing import Optional

from caerp.controllers.task.estimation import EstimationInvoicingController
from caerp.controllers.task.invoice import gen_common_invoice_from_invoice
from caerp.models.task.estimation import Estimation
from caerp.services.business import get_sold_deadlines


def gen_invoice_from_payment_deadline(
    request,
    business,
    payment_deadline,
    add_estimation_details=False,
):
    controller = EstimationInvoicingController(payment_deadline.estimation, request)
    if payment_deadline.deposit:
        invoice = controller.gen_deposit_invoice(
            request.identity,
            payment_deadline.description,
            payment_deadline.amount_ttc,
            date=payment_deadline.date,
            add_estimation_details=add_estimation_details,
        )
    elif payment_deadline in get_sold_deadlines(request, business):
        return gen_sold_invoice(request, business, payment_deadline)
    else:
        invoice = controller.gen_intermediate_invoice(
            request.identity,
            payment_deadline.description,
            payment_deadline.amount_ttc,
            date=payment_deadline.date,
            add_estimation_details=add_estimation_details,
        )
    payment_deadline.invoice_id = invoice.id
    request.dbsession.merge(payment_deadline)
    return invoice


def gen_new_intermediate_invoice(
    request,
    business,
    estimation: Optional[Estimation] = None,
    add_estimation_details: bool = False,
):
    """
    Génère une nouvelle facture intermédiaire pour l'affaire

    Si on a un devis, on l'utilise comme référence pour la nouvelle facture

    Sinon on utilise une facture pour récupérer les informations générales
    (project_id, customer_id ...)
    """
    if business.estimations:
        if estimation is None:
            estimation = business.estimations[-1]
        controller = EstimationInvoicingController(estimation, request)
        return controller.gen_intermediate_invoice(
            request.identity,
            "Nouvelle facture",
            0,
            add_estimation_details=add_estimation_details,
        )
    elif business.invoices:
        ref_invoice = business.invoices[0]
        return gen_common_invoice_from_invoice(request, request.identity, ref_invoice)
    else:
        raise Exception("Business must have at least one estimation or invoice")


def gen_sold_invoice(
    request, business, payment_deadline=None, ignore_previous_invoices=False
):
    if payment_deadline is None:
        payment_deadline = business.payment_deadlines[-1]
    controller = EstimationInvoicingController(payment_deadline.estimation, request)
    invoice = controller.gen_sold_invoice(
        request.identity,
        date=payment_deadline.date,
        ignore_previous_invoices=ignore_previous_invoices,
    )
    payment_deadline.invoice_id = invoice.id
    request.dbsession.merge(payment_deadline)
    return invoice

from sqlalchemy import select
from sqlalchemy.orm import aliased

from caerp.models.price_study.base import BasePriceStudyProduct
from caerp.models.price_study.chapter import PriceStudyChapter
from caerp.models.price_study.discount import PriceStudyDiscount
from caerp.models.task import DiscountLine, TaskLine, TaskLineGroup
from caerp.models.task.invoice import Invoice


def is_invoice_canceled(request, invoice: Invoice) -> bool:
    """
    Check if an invoice has been canceled with a CancelInvoice
    """
    if invoice.paid_status != "resulted":
        return False

    if len(invoice.payments) == 0:
        return True

    if sum([payment.amount for payment in invoice.payments]) == 0:
        return True
    return False


def invoice_has_modification(request, invoice: Invoice) -> bool:
    """
    Check if one the invoice's elements has modified set to True
    """
    if invoice.price_study is not None:
        aliased_chapter = aliased(PriceStudyChapter)
        query1 = (
            select(BasePriceStudyProduct.id)
            .join(
                aliased_chapter, BasePriceStudyProduct.chapter_id == aliased_chapter.id
            )
            .where(
                BasePriceStudyProduct.modified.is_(True),
                aliased_chapter.price_study_id == invoice.price_study.id,
            )
            .exists()
        )
        query2 = (
            select(PriceStudyDiscount.id)
            .where(
                PriceStudyDiscount.modified.is_(True),
                PriceStudyDiscount.id == invoice.price_study.id,
            )
            .exists()
        )
    else:
        aliased_group = aliased(TaskLineGroup)
        query1 = (
            select(TaskLine.id)
            .join(aliased_group, TaskLine.group_id == aliased_group.id)
            .where(
                TaskLine.modified.is_(True),
                aliased_group.task_id == invoice.id,
            )
            .exists()
        )
        query2 = (
            select(DiscountLine.id)
            .where(
                DiscountLine.modified.is_(True),
                aliased_group.task_id == invoice.id,
            )
            .exists()
        )
    return (
        request.dbsession.execute(select(query2)).scalar()
        or request.dbsession.execute(select(query1)).scalar()
    )

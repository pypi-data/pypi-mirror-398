import logging
from typing import Optional, Union

from caerp.compute.math_utils import convert_to_int
from caerp.controllers.price_study.price_study import (
    price_study_sync_amounts,
    price_study_sync_with_task,
)
from caerp.forms import price_study
from caerp.models.config import Config
from caerp.models.price_study.chapter import PriceStudyChapter
from caerp.models.sale_product.base import BaseSaleProduct
from caerp.models.sale_product.work import SaleProductWork
from caerp.models.sale_product.work_item import WorkItem
from caerp.models.task.estimation import Estimation
from caerp.models.task.task import Task, TaskLine, TaskLineGroup
from caerp.models.tva import Product, Tva

logger = logging.getLogger(__name__)


def get_task_params_from_other_task(request, user, task: Task) -> dict:
    """
    Get task parameters from another task.
    Can be used to generate invoice from estimation, or create an invoice into
    a same business ...

    Args:
        request: The current request object.
    """
    return dict(
        user=user,
        company=task.company,
        project=task.project,
        phase_id=task.phase_id,
        payment_conditions=task.payment_conditions,
        address=task.address,
        workplace=task.workplace,
        mentions=[mention for mention in task.mentions if mention.active],
        company_mentions=[
            mention for mention in task.company_mentions if mention.active
        ],
        business_type_id=task.business_type_id,
        mode=task.mode,
        display_ttc=task.display_ttc,
        decimal_to_display=task.decimal_to_display,
        business_id=task.business_id,
    )


def _set_tva(request, collection, tva: Tva):
    for obj in collection:
        obj.tva = tva
        request.dbsession.merge(obj)


def _set_tva_and_product(request, collection, tva: Tva, product: Optional[Product]):
    for obj in collection:
        obj.tva = tva
        obj.product = product
        request.dbsession.merge(obj)


def bulk_edit_tva_and_product_id(
    request,
    context: Union[TaskLineGroup, PriceStudyChapter, Task],
    tva: Tva,
    product: Optional[Product],
) -> None:
    if isinstance(context, Task):
        task = context
        if context.has_price_study():
            price_study = context.price_study
            _set_tva_and_product(request, price_study.products, tva, product)
            _set_tva(request, price_study.discounts, tva)
        else:
            _set_tva_and_product(request, context.all_lines, tva, product)
            _set_tva(request, context.discounts, tva)
    elif isinstance(context, PriceStudyChapter):
        task = context.price_study.task
        _set_tva_and_product(request, context.products, tva, product)
    elif isinstance(context, TaskLineGroup):
        task = context.task
        _set_tva_and_product(request, context.lines, tva, product)
    else:
        raise ValueError(f"Unsupported context type {context.__class__.__name__}")


def _set_tva_and_product_from_catalog(
    request,
    task_line: TaskLine,
    sale_product_entry: BaseSaleProduct,
    document: Optional[Task] = None,
):
    from caerp.services.tva import get_task_default_tva_and_product

    if document:
        if not document.internal and sale_product_entry.tva:
            tva = sale_product_entry.tva
            product = sale_product_entry.product
        else:
            tva, product = get_task_default_tva_and_product(
                request, internal=document.internal
            )
    else:
        if sale_product_entry.tva:
            tva = sale_product_entry.tva
            product = sale_product_entry.product
        else:
            tva, product = get_task_default_tva_and_product(request, internal=False)
    task_line.tva = tva
    task_line.product = product


def taskline_from_sale_product(
    request,
    sale_product: BaseSaleProduct,
    quantity: Optional[float] = 1,
    document: Optional[Task] = None,
) -> TaskLine:
    result = TaskLine()
    result.description = sale_product.get_taskline_description()
    if document:
        mode = document.mode
    else:
        mode = "ht"

    if mode == "ht":
        result.cost = sale_product.ht
    else:
        result.cost = sale_product.ttc

    result.mode = mode
    result.unity = sale_product.unity
    result.quantity = quantity
    _set_tva_and_product_from_catalog(request, result, sale_product, document)
    return result


def taskline_from_sale_product_work_item(
    request,
    work_item: WorkItem,
    document: Optional[Task] = None,
    quantity: Optional[float] = 1,
):
    result = TaskLine()
    result.description = work_item.description

    if document:
        mode = document.mode
    else:
        mode = "ht"

    if mode == "ht":
        result.cost = work_item.ht
    else:
        result.cost = work_item.total_ttc()
    result.mode = mode
    result.unity = work_item.unity
    result.quantity = quantity * work_item.quantity
    _set_tva_and_product_from_catalog(
        request, result, work_item.sale_product_work, document
    )
    return result


def tasklinegroup_from_sale_product_work(
    request,
    sale_product_work: SaleProductWork,
    document: Optional[Task] = None,
    quantity: Optional[float] = 1,
) -> TaskLineGroup:
    logger.debug("Creating tasklinegroup from sale_product_work %s", sale_product_work)
    logger.debug(sale_product_work.items)
    group = TaskLineGroup()
    group.title = sale_product_work.title
    group.description = sale_product_work.get_taskline_description()
    request.dbsession.add(group)
    request.dbsession.flush()

    for item in sale_product_work.items:
        line = taskline_from_sale_product_work_item(
            request,
            item,
            document=document,
            quantity=quantity,
        )
        line.group_id = group.id
        group.lines.append(line)
    return group


def task_on_before_commit(
    request, task: Task, action: str, attributes: Optional[dict] = None
):
    if action == "update":
        if attributes:
            if (
                attributes
                and "insurance_id" in attributes
                and task.has_price_study()
                and Config.get_value(
                    "price_study_uses_insurance", default=True, type_=bool
                )
            ):
                logger.debug("Insurance id changed Syncing EDP")
                price_study_sync_amounts(request, task.price_study, sync_down=True)
                price_study_sync_with_task(request, task.price_study)
            if "tva_id" in attributes:
                task.cache_totals(request)

            # Cas du devis
            if (
                isinstance(task, Estimation)
                and "payment_times" in attributes
                or "deposit" in attributes
            ):
                payment_times = attributes.get("payment_times", None)
                payment_times = convert_to_int(payment_times, default=None)
                task.update_payment_lines(  # pyright: ignore[reportAttributeAccessIssue]
                    request, payment_times
                )

    if action == "delete":
        task.business.on_task_delete(request, task)
    return task

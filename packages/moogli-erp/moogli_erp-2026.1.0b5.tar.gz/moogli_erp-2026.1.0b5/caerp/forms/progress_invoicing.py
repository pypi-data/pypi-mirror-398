"""
Form schemas used to edit an Invoice in progress_invoicing edition mode
"""
import logging
from typing import Union

import colander
import colanderalchemy

from caerp import forms
from caerp.compute import math_utils
from caerp.forms.custom_types import QuantityType
from caerp.forms.tasks.task import get_new_task_name
from caerp.models.progress_invoicing import (
    ProgressInvoicingProduct,
    ProgressInvoicingWork,
    ProgressInvoicingWorkItem,
)
from caerp.models.progress_invoicing.invoicing import (
    ProgressInvoicingChapter,
    ProgressInvoicingPlan,
)
from caerp.models.task import Invoice
from caerp.models.task.invoice import CancelInvoice
from caerp.services.progress_invoicing import (
    get_chapter_min_percentage,
    get_progress_invoicing_plan_min_percentage,
)

logger = logging.getLogger(__name__)


def force_two_digits_percent(value):
    """
    Limit a float entry to two digits
    """
    return math_utils.round(value, 2)


@colander.deferred
def deferred_percent_validator(node, kw):
    """
    Return a percent validator for the given context edition
    regarding if it's attached to an Invoice or a CancelInvoice
    """
    context = kw["request"].context
    already_invoiced = context.already_invoiced or 0
    if isinstance(context.task, Invoice):
        to_invoice = math_utils.round(100 - already_invoiced, 2)
        return colander.Range(0, to_invoice)
    else:
        invoiced = already_invoiced
        return colander.Range(-1 * invoiced, 0)


def get_edit_product_schema():
    """
    Build an edition schema used to validate the Product edition

    :returns: An colanderalchemy SQLAlchemySchemaNode object
    """
    schema = colanderalchemy.SQLAlchemySchemaNode(
        ProgressInvoicingProduct,
        includes=(
            "id",
            "percentage",
        ),
    )
    forms.customize_field(
        schema,
        "percentage",
        typ=QuantityType(),
        validator=deferred_percent_validator,
        preparer=force_two_digits_percent,
    )
    return schema


def get_edit_work_schema():
    """
    Build an edition schema used to validate the Work edition

    :returns: An colanderalchemy SQLAlchemySchemaNode object
    """
    schema = colanderalchemy.SQLAlchemySchemaNode(
        ProgressInvoicingWork, includes=("id", "percentage", "locked")
    )
    forms.customize_field(
        schema,
        "percentage",
        typ=QuantityType(),
        validator=deferred_percent_validator,
        preparer=force_two_digits_percent,
    )
    return schema


def get_edit_workitem_schema():
    """
    Build an edition schema used to validate the WorkItem edition

    :returns: An colanderalchemy SQLAlchemySchemaNode object
    """
    schema = colanderalchemy.SQLAlchemySchemaNode(
        ProgressInvoicingWorkItem,
        includes=(
            "id",
            "_percentage",
        ),
    )

    forms.customize_field(
        schema,
        "_percentage",
        typ=QuantityType(),
        validator=deferred_percent_validator,
        preparer=force_two_digits_percent,
    )
    return schema


@colander.deferred
def deferred_default_name(node, kw):
    request = kw["request"]
    business = request.context
    return get_new_task_name(request, Invoice, business=business)


class NewInvoiceSchema(colander.Schema):
    name = colander.SchemaNode(
        colander.String(),
        title="Nom du document",
        description="Ce nom n'apparaît pas dans le document final",
        validator=colander.Length(max=255),
        default=deferred_default_name,
        missing="Facture",
    )


def get_new_invoice_schema():
    """
    Build a colander schema for invoice add in progressing mode
    """
    return NewInvoiceSchema()


def get_percentage_validator(request, context):
    """
    Return a percent validator for the given context edition
    regarding if it's attached to a Plan or a Chapter
    """

    min_percentage = 0
    if isinstance(context, ProgressInvoicingPlan):
        min_percentage = get_progress_invoicing_plan_min_percentage(request, context)
    else:
        min_percentage = get_chapter_min_percentage(request, context)

    context_task = context.task
    is_cancelinvoice = isinstance(context_task, CancelInvoice)

    if is_cancelinvoice:
        return colander.Range(-100, -1 * min_percentage)
    else:
        return colander.Range(min_percentage, 100)


def get_percentage_schema(
    request, context=Union[ProgressInvoicingPlan, ProgressInvoicingChapter]
):
    class BulkEditSchema(colander.Schema):
        percentage = colander.SchemaNode(
            QuantityType(),
            title="Pourcentage",
            validator=get_percentage_validator(request, context),
            preparer=force_two_digits_percent,
        )

    return BulkEditSchema()

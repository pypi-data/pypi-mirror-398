from caerp.models.progress_invoicing.invoicing import (
    ProgressInvoicingChapter,
    ProgressInvoicingPlan,
    ProgressInvoicingWork,
)


def get_chapter_min_percentage(request, chapter: ProgressInvoicingChapter) -> float:
    """
    Renvoie le pourcentage maximum que l'on peut configurer sur ce chapitre
    """
    percentage = 0
    for product in chapter.products:
        if isinstance(product, ProgressInvoicingWork) and not product.locked:
            for work_item in product.items:
                already_invoiced = work_item.already_invoiced or 0
                percentage = max(percentage, already_invoiced)
        else:
            already_invoiced = product.already_invoiced or 0
            percentage = max(percentage, already_invoiced)
    return percentage


def get_progress_invoicing_plan_min_percentage(
    request, progress_invoicing_plan: ProgressInvoicingPlan
) -> float:
    """
    Renvoie le pourcentage maximum d'avancement configurable sur ce plan
    d'avancement
    """
    percentage = 0
    for chapter in progress_invoicing_plan.chapters:
        percentage = max(get_chapter_min_percentage(request, chapter), percentage)
    return percentage

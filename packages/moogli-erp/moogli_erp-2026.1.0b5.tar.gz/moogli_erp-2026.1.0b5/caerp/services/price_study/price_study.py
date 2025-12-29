from typing import Optional, Union

from caerp.models.price_study.chapter import PriceStudyChapter
from caerp.models.price_study.discount import PriceStudyDiscount
from caerp.models.price_study.price_study import PriceStudy
from caerp.models.price_study.product import PriceStudyProduct
from caerp.models.price_study.work import PriceStudyWork
from caerp.models.price_study.work_item import PriceStudyWorkItem
from caerp.models.task.task import Task


def get_related_task(
    request,
    model_instance: Union[
        PriceStudy,
        PriceStudyChapter,
        PriceStudyDiscount,
        PriceStudyProduct,
        PriceStudyWork,
        PriceStudyWorkItem,
    ],
) -> Optional[Task]:
    related_task = None
    if isinstance(model_instance, PriceStudy):
        related_task = model_instance.task
    elif isinstance(
        model_instance,
        (PriceStudyChapter, PriceStudyProduct, PriceStudyDiscount, PriceStudyWork),
    ):
        if model_instance.price_study:
            related_task = model_instance.price_study.task
    elif isinstance(model_instance, PriceStudyWorkItem):
        if model_instance.price_study_work:
            related_task = get_related_task(request, model_instance.price_study_work)
    return related_task

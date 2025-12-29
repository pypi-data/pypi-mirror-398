from typing import List, Optional, Tuple

from sqlalchemy import exists, select
from sqlalchemy.orm import load_only

from caerp.models.task.task import Task, TaskLine
from caerp.models.tva import Product, Tva


def get_tva_by_value(request, tva_value, only_active=True):
    """
    Retrieve the Tva object associated with the given value.
    """
    query = select(Tva).where(Tva.value == tva_value)
    if only_active:
        query = query.where(Tva.active.is_(True))
    return request.dbsession.execute(query).scalar()


def get_tva_by_id(request, tva_id, only_active=True):
    """
    Retrieve the Tva object associated with the given ID.
    """
    query = select(Tva).where(Tva.id == tva_id)
    if only_active:
        query = query.where(Tva.active.is_(True))
    return request.dbsession.execute(query).scalar()


def get_product_by_id(request, product_id, only_active=True):
    """
    Retrieve the Product object associated with the given ID.
    """
    query = select(Product).where(Product.id == product_id)
    if only_active:
        query = query.where(Product.active.is_(True))
    return request.dbsession.execute(query).scalar()


def get_tva_and_product_from_ids(
    request, tva_id: int, product_id: Optional[int] = None
) -> Tuple[Tva, Optional[Product]]:
    """
    Fetch and validate the couple Tva / Product based on the provided IDs.

    :raises: Exception if either TVA or Product ID is invalid or do not match.
    """
    tva = get_tva_by_id(request, tva_id)
    if tva is None:
        raise Exception("Invalid TVA ID")
    if product_id is not None:
        product = get_product_by_id(request, product_id)
        if product is None:
            raise Exception("Invalid Product ID")
        if product.tva_id != tva_id:
            raise Exception("Product does not match the TVA")
    else:
        product = None
    return tva, product


def get_tvas(
    request,
    attribute_name: Optional[str] = None,
    internal: bool = False,
    active=True,
) -> List[Tva]:
    """
    Retrieve all active Tva.
    """
    query = select(Tva).join(Product)
    if active:
        query = query.where(Tva.active.is_(True))
    if attribute_name is not None:
        query = query.options(load_only(getattr(Tva, attribute_name)))

    query = query.where(Product.internal.is_(internal))
    query = query.order_by(Tva.value)
    query = query.distinct()
    return request.dbsession.execute(query).scalars().all()


def get_products(
    request,
    attribute_name: Optional[str] = None,
    internal: bool = False,
    active=True,
) -> List[Product]:
    """
    Retrieve all active Products.
    """
    query = select(Product)
    if active:
        query = query.where(Product.active.is_(True))
    if attribute_name is not None:
        query = query.options(load_only(getattr(Product, attribute_name)))
    query = query.filter(Product.internal.is_(internal))
    return request.dbsession.execute(query).scalars().all()


def is_tva_used(request, tva: Tva) -> bool:
    """
    Check if the Tva is used by any product.
    """
    query = exists().select(TaskLine.id).filter(TaskLine.tva_id == tva.id)
    return request.dbsession.execute(query).scalar() is True


def get_task_default_tva(
    request, task: Optional[Task] = None, internal: bool = False
) -> Optional[Tva]:
    """
    get the default tva for the given task
    """
    if task is not None:
        internal = task.internal
    # On récupère la liste des TVA possibles
    tvas = get_tvas(request, internal=internal)
    # On utilise la dernière TVA du doc si elle fait partie des TVA possibles
    if task and len(task.all_lines) > 0:
        last_tva = task.all_lines[-1].tva
        if last_tva and last_tva in tvas:
            return last_tva

    # On recherche la tva par défaut si elle existe
    for tva in tvas:
        if tva.default:
            return tva

    # On renvoie la première TVA si elle existe
    return tvas[0] if tvas else None


def has_default_tva(request) -> bool:
    """
    Check if there is an active default tva.
    """
    return (
        request.dbsession.execute(
            exists().select(Tva.id).filter(Tva.default.is_(True), Tva.active.is_(True))
        ).scalar()
        is True
    )


def get_task_default_product(
    request,
    task: Optional[Task] = None,
    internal: bool = False,
    default_tva: Optional[Tva] = None,
) -> Optional[Product]:
    if task:
        internal = task.internal

    if default_tva is None:
        default_tva = get_task_default_tva(request, task, internal)

    if default_tva and len(default_tva.products) == 1:
        return default_tva.products[0]

    products = get_products(request, internal=internal)
    if len(products) == 1:
        return products[0]
    return None


def get_task_default_tva_and_product(
    request, task: Optional[Task] = None, internal: bool = False
) -> Tuple[Optional[Tva], Optional[Product]]:
    default_tva = get_task_default_tva(request, task, internal=internal)
    default_product = get_task_default_product(
        request, task, internal=internal, default_tva=default_tva
    )
    return default_tva, default_product

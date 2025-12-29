"""
Supplier handling forms schemas and related widgets
"""
import functools

import colander
import deform
from colanderalchemy import SQLAlchemySchemaNode
from sqlalchemy import or_
from sqlalchemy.orm import contains_eager

from caerp import forms
from caerp.compute.math_utils import convert_to_int
from caerp.forms.company import company_filter_node_factory
from caerp.forms.lists import BaseListsSchema
from caerp.forms.third_party.base import (
    build_admin_third_party_options,
    build_third_party_values,
    get_company_third_party_schema,
    get_individual_third_party_schema,
    get_internal_third_party_schema,
)
from caerp.models.company import Company
from caerp.models.expense.sheet import ExpenseLine, ExpenseSheet
from caerp.models.project import Project
from caerp.models.supply import SupplierInvoice, SupplierOrder
from caerp.models.third_party.supplier import Supplier


def get_company_suppliers_from_request(request):
    """
    Extract a suppliers list from the request object

    :param obj request: The pyramid request object
    :returns: A list of suppliers
    :rtype: list
    """
    internal = False
    if isinstance(request.context, Project):
        company_id = request.context.company.id
    elif isinstance(request.context, Company):
        company_id = request.context.id
    elif isinstance(request.context, SupplierInvoice):
        if len(request.context.supplier_orders) > 0:
            return [request.context.supplier_orders[0].supplier]
        else:
            company_id = request.context.company.id
        internal = request.context.internal
    elif isinstance(request.context, SupplierOrder):
        company_id = request.context.company.id
        internal = request.context.internal
    elif isinstance(request.context, ExpenseLine):
        company_id = request.context.sheet.company_id
        internal = None
    elif isinstance(request.context, ExpenseSheet):
        company_id = request.context.company_id
        internal = None

    else:
        return []

    suppliers = Supplier.label_query()
    suppliers = suppliers.filter_by(company_id=company_id)
    suppliers = suppliers.filter_by(archived=False)

    if internal is not None:
        if internal:
            suppliers = suppliers.filter(Supplier.type == "internal")
        else:
            suppliers = suppliers.filter(Supplier.type != "internal")

    return suppliers.order_by(Supplier.label).all()


def _get_globalizable_suppliers(request):
    query = Supplier.label_query()  # FIXME: dédoublonner
    query = query.filter(or_(Supplier.siret != "", Supplier.registration != ""))
    return query


def _get_suppliers_for_filters_from_request(request, is_global=False):
    """
    Extract a suppliers list from the request object in order to build up a
    supplier filter

    :param obj request: The Pyramid request object
    :param bool is_global: Do we request all CAE suppliers ?

    :returns: A SQLAlchemy query
    """
    context = request.context
    query = Supplier.label_query()
    # Fournisseurs d'une enseigne
    if isinstance(context, Company):
        query = query.filter_by(company_id=context.id)
    # Fournisseurs de la CAE
    elif is_global:
        query = query.join(Supplier.company)
        query = query.options(contains_eager(Supplier.company).load_only("name"))
    else:
        raise Exception("Unsupported context {} (not Company)".format(context))
    return query


def get_current_supplier_id_from_request(request):
    """
    Return the current supplier from the request object

    :param obj request: The current pyramid request object
    """
    result = None
    if "supplier" in request.params:
        result = convert_to_int(request.params.get("supplier"))
    return result


def get_deferred_supplier_select(
    query_func=get_company_suppliers_from_request,
    item_builder=build_third_party_values,
    default_option=None,
    **widget_options,
):
    """
    Dynamically build a deferred supplier select with (or without) a void
    default value

    :param function query_func: The query builder to get the suppliers (gets
    request as argument)
    :param function item_builder: a function user
    :param 2-uple default_option: A default option to insert in the select
    options

    :returns: A deferred supplier Select2Widget
    """

    @colander.deferred
    def deferred_supplier_select(node, kw):
        """
        Collecting supplier select datas from the given request's context

        :param dict kw: Binding dict containing a request key
        :returns: A deform.widget.Select2Widget
        """
        request = kw["request"]
        suppliers = query_func(request)
        values = list(item_builder(suppliers))
        if default_option is not None:
            # Cleaner fix would be to replace `default_option` 2-uple arg with
            # a `placeholder` str arg, as in JS code.
            # Use of placeholder arg is mandatory with Select2 ; otherwise, the
            # clear button crashes. https://github.com/select2/select2/issues/5725
            values.insert(0, default_option)
            widget_options["placeholder"] = default_option[1]

        return deform.widget.Select2Widget(values=values, **widget_options)

    return deferred_supplier_select


def get_deferred_default_supplier(query_func):
    @colander.deferred
    def deferred_default_supplier(node, kw):
        """
        Collect the default supplier value from a request's context

        :param dict kw: Binding dict containing a request key
        :returns: The current supplier or colander.null
        """
        request = kw["request"]
        supplier_id = get_current_supplier_id_from_request(request)
        result = colander.null
        if supplier_id is not None:
            # On checke pour éviter de se faire avoir si le supplier est passé
            # en paramètre
            suppliers = query_func(request)
            if supplier_id in [c.id for c in suppliers]:
                result = supplier_id
        return result

    return deferred_default_supplier


def get_deferred_supplier_select_validator(
    query_func=get_company_suppliers_from_request,
):
    @colander.deferred
    def _deferred_supplier_validator(node, kw):
        """
        Build a supplier option validator based on the request's context

        :param dict kw: Binding dict containing a request key
        :returns: A colander validator
        """
        request = kw["request"]
        suppliers = query_func(request)
        supplier_ids = [supplier.id for supplier in suppliers]

        def supplier_oneof(value):
            if value in ("0", 0):
                return "Veuillez choisir un fournisseur"
            elif value not in supplier_ids:
                return "Entrée invalide"
            return True

        return colander.Function(supplier_oneof)

    return _deferred_supplier_validator


def _base_supplier_choice_node_factory(**kw):
    """
    Shortcut used to build a colander schema node

    all arguments are optionnal

    Allow following options :

        any key under kw

            colander.SchemaNode options :

                * title,
                * description,
                * default,
                * missing
                * ...

        widget_options

            deform.widget.Select2Widget options as a dict

        query_func

            A callable expecting the request parameter and returning
            the current supplier that should be selected

    e.g:

        >>> get_company_suppliers_from_request(
            title="Fournisseur",
            query_func=get_suppliers_list,
            default=get_current_supplier,
            widget_options={}
        )


    """
    title = kw.pop("title", "")
    query_func = kw.pop("query_func", get_company_suppliers_from_request)
    default = kw.pop("default", get_deferred_default_supplier(query_func))
    widget_options = kw.pop("widget_options", {})
    return colander.SchemaNode(
        colander.Integer(),
        title=title,
        default=default,
        widget=get_deferred_supplier_select(query_func=query_func, **widget_options),
        validator=get_deferred_supplier_select_validator(query_func),
        **kw,
    )


def _base_supplier_filter_node_factory(is_global=False, widget_options=None, **kwargs):
    """
    return a supplier selection node

        is_global

            is the associated view restricted to company's invoices
    """
    widget_options = widget_options or {}
    default_option = widget_options.pop("default_option", None)

    # On pré-remplie la fonction _get_suppliers_for_filters_from_request
    query_func = functools.partial(
        _get_suppliers_for_filters_from_request,
        is_global=is_global,
    )

    if is_global:
        deferred_supplier_validator = None
        item_builder = widget_options.pop(
            "item_builder",
            build_admin_third_party_options,
        )
    else:
        deferred_supplier_validator = get_deferred_supplier_select_validator(query_func)
        item_builder = widget_options.pop(
            "item_builder",
            build_third_party_values,
        )

    return colander.SchemaNode(
        colander.Integer(),
        widget=get_deferred_supplier_select(
            query_func=query_func,
            item_builder=item_builder,
            default_option=default_option,
        ),
        validator=deferred_supplier_validator,
        **kwargs,
    )


# Supplier choice node : utilisé dans les formulaires:
# Liste des fournisseurs :
# 1- Tous ceux de l'enseigne avec ceux du dossier courant en premier
# 2- Tous ceux de l'enseigne
supplier_choice_node_factory = forms.mk_choice_node_factory(
    _base_supplier_choice_node_factory,
    title="Choix du fournisseur",
    resource_name="un fournisseur",
)


def _build_items_with_registration(suppliers):

    return [
        (x.id, "{} ({})".format(x.label, x.get_company_identification_number()))
        for x in suppliers
    ]


# Liste globale de fournisseurs
#
# On ne conserve que ceux qui sont « globalisables » : possédant un n°
# d'imatriculation (SIRET/SIREN…)
globalizable_supplier_choice_node_factory = forms.mk_choice_node_factory(
    _base_supplier_choice_node_factory,
    title="Choix du fournisseur",
    resource_name="un fournisseur",
    query_func=_get_globalizable_suppliers,
    widget_options={"item_builder": _build_items_with_registration},
)


# Supplier filter node : utilisé dans les listview
# 1- Tous les fournisseurs
# 2- Tous les fournisseurs d'une entreprise
supplier_filter_node_factory = forms.mk_filter_node_factory(
    _base_supplier_filter_node_factory,
    title="Fournisseur",
    empty_filter_msg="Tous",
)


def get_list_schema(is_global=False):
    """
    Return the schema for the supplier search list
    """
    schema = BaseListsSchema().clone()
    schema["search"].title = "Recherche"
    schema["search"].description = "Raison sociale, contact, ou SIREN"
    if is_global:
        schema.add_before(
            "items_per_page", company_filter_node_factory(name="company_id")
        )
    schema.add(
        colander.SchemaNode(
            colander.Boolean(),
            name="archived",
            label="Inclure les fournisseurs archivés",
            title="",
        )
    )
    if not is_global:
        schema.add(
            colander.SchemaNode(
                colander.Boolean(),
                name="internal",
                label="Inclure les enseignes internes",
                title="",
                default=False,
            )
        )
    return schema


def get_global_list_schema():
    schema = BaseListsSchema().clone()
    schema["search"].title = "Recherche"
    schema["search"].description = "Raison sociale ou SIREN"
    return schema


def get_individual_supplier_schema():
    return get_individual_third_party_schema(Supplier)


def get_company_supplier_schema():
    return get_company_third_party_schema(Supplier)


def get_internal_supplier_schema(edit=False):
    return get_internal_third_party_schema(Supplier, edit)


def get_set_global_accounting_schema():
    """
    Renvoie un schéma pour l'édition des comptes comptables fournisseurs
    """

    class MySchema(colander.Schema):
        compte_cg = colander.SchemaNode(
            colander.String(),
            title="Compte comptable",
            description="Compte comptable associé à appliquer à ce fournisseur",
            missing=colander.drop,
            validator=colander.Length(
                max=125,
                max_err="Le compte général ne doit pas dépasser 125 caractères",
            ),
        )
        compte_tiers = colander.SchemaNode(
            colander.String(),
            title="Compte tiers",
            description="Compte tiers associé à appliquer à ce fournisseur",
            missing=colander.drop,
            validator=colander.Length(
                max=125, max_err="Le compte tiers ne doit pas dépasser 125 caractères"
            ),
        )

    return MySchema()

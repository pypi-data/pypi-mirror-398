import logging

import colander
from sqlalchemy import not_, or_
from sqlalchemy.orm import undefer_group

from caerp.consts.permissions import PERMISSIONS
from caerp.forms.third_party.supplier import get_list_schema
from caerp.models.company import Company
from caerp.models.third_party.supplier import Supplier
from caerp.utils.widgets import Link, POSTButton
from caerp.views import BaseCsvView, BaseListView, TreeMixin

from .routes import (
    CAE_SUPPLIERS_ROUTE,
    COMPANY_SUPPLIERS_ADD_ROUTE,
    COMPANY_SUPPLIERS_ROUTE,
    GLOBAL_SUPPLIERS_ROUTE,
    SUPPLIER_ITEM_ROUTE,
)

logger = log = logging.getLogger(__name__)


class SuppliersListTools:
    title = "Liste des fournisseurs"
    schema = get_list_schema()
    sort_columns = {
        "label": Supplier.label,
        "company_name": Supplier.company_name,
        "created_at": Supplier.created_at,
    }
    default_sort = "created_at"
    default_direction = "desc"

    def query(self):
        query = self.request.dbsession.query(Supplier)
        return query

    def filter_company(self, query, appstruct):
        company = self.request.context
        return query.filter(Supplier.company_id == company.id)

    def filter_archived(self, query, appstruct):
        archived = appstruct.get("archived", False)
        if archived in (False, colander.null, "false"):
            query = query.filter_by(archived=False)
        return query

    def filter_name_or_contact(self, records, appstruct):
        """
        Filter the records by supplier name or contact lastname
        """
        search = appstruct.get("search")
        if search:
            records = records.filter(
                or_(
                    Supplier.company_name.like("%" + search + "%"),
                    Supplier.internal_name.like("%" + search + "%"),
                    Supplier.lastname.like("%" + search + "%"),
                    Supplier.siret.like("%" + search + "%"),
                    Supplier.registration.like("%" + search + "%"),
                )
            )
        return records

    def filter_internal(self, query, appstruct):
        include_internal = appstruct.get("internal", True)
        if include_internal in (False, colander.null, "false"):
            query = query.filter(not_(Supplier.type == "internal"))
        return query


class SuppliersListView(SuppliersListTools, BaseListView, TreeMixin):
    is_global = False
    route_name = COMPANY_SUPPLIERS_ROUTE
    item_route_name = SUPPLIER_ITEM_ROUTE
    add_template_vars = (
        "stream_actions",
        "title",
        "stream_main_actions",
        "stream_more_actions",
    )

    @property
    def tree_url(self):
        """
        Compile the url to be used in the breadcrumb for this view

        The context can be either :

        - A Company
        - A Supplier
        - A Task
        """
        if isinstance(self.context, Company):
            cid = self.context.id
        elif isinstance(self.context, Supplier):
            cid = self.context.company_id
        else:
            raise Exception(
                "Can't retrieve company id for breadcrumb generation %s"
                % (self.context,)
            )
        return self.request.route_path(self.route_name, id=cid)

    def stream_main_actions(self):
        if self.request.has_permission(PERMISSIONS["context.add_supplier"]):
            yield Link(
                self.request.route_path(
                    COMPANY_SUPPLIERS_ADD_ROUTE, id=self.context.id
                ),
                label="Ajouter<span class='no_mobile'>&nbsp;un fournisseur</span>",
                icon="plus",
                css="btn btn-primary",
                title="Ajouter un nouveau fournisseur",
            )
            yield Link(
                self.request.route_path(
                    "company_suppliers_import_step1", id=self.context.id
                ),
                label="Importer<span class='no_mobile'>&nbsp;des fournisseurs</span>",
                title="Importer des fournisseurs",
                icon="file-import",
                css="btn icon",
            )

    def stream_more_actions(self):
        if self.request.has_permission(PERMISSIONS["context.add_supplier"]):
            yield Link(
                self.request.route_path("suppliers.csv", id=self.context.id),
                label="<span class='no_mobile no_tablet'>Exporter les fournisseurs au format&nbsp;"
                "</span>CSV",
                title="Exporter les fournisseurs au format CSV",
                icon="file-csv",
                css="btn icon_only_mobile",
            )

    def stream_actions(self, supplier):
        """
        Return action buttons with permission handling
        """

        if self.request.has_permission(
            PERMISSIONS["context.delete_supplier"], supplier
        ):
            yield POSTButton(
                self.request.route_path(
                    SUPPLIER_ITEM_ROUTE,
                    id=supplier.id,
                    _query=dict(action="delete"),
                ),
                "Supprimer",
                title="Supprimer définitivement ce fournisseur",
                icon="trash-alt",
                css="negative",
                confirm="Êtes-vous sûr de vouloir supprimer ce fournisseur ?",
            )

        yield Link(
            self.request.route_path(SUPPLIER_ITEM_ROUTE, id=supplier.id),
            "Voir ce fournisseur",
            title="Voir ou modifier ce fournisseur",
            icon="arrow-right",
        )

        if supplier.archived:
            label = "Désarchiver"
        else:
            label = "Archiver"
        yield POSTButton(
            self.request.route_path(
                SUPPLIER_ITEM_ROUTE,
                id=supplier.id,
                _query=dict(action="archive"),
            ),
            label,
            icon="archive",
        )

    def _build_return_value(self, schema, appstruct, query):
        result = super()._build_return_value(schema, appstruct, query)
        result["is_global"] = self.is_global
        return result


"""
Liste consolidée des fournisseurs unitaires pour la CAE

> Conservée par sécurité mais remplacée par la GlobalSuppliersListView()
"""


class CaeSuppliersListView(SuppliersListView):
    is_global = True
    title = "Liste des fournisseurs de la CAE"
    schema = get_list_schema(is_global=True)
    route_name = CAE_SUPPLIERS_ROUTE

    @property
    def tree_url(self):
        return self.request.route_path(CAE_SUPPLIERS_ROUTE)

    def filter_company(self, query, appstruct):
        company_id = appstruct.get("company_id", None)
        if company_id:
            query = query.filter(Supplier.company_id == company_id)
        return query

    def filter_internal(self, query, appstruct):
        return query.filter(not_(Supplier.type == "internal"))

    def stream_main_actions(self):
        yield Link(
            self.request.route_path(GLOBAL_SUPPLIERS_ROUTE),
            label="Référenciel fournisseur commun",
            title="Voir le référenciel fournisseur commun de la CAE",
            icon="users",
            css="btn icon",
        )

    def stream_more_actions(self):
        return ()

    def stream_actions(self, supplier):
        yield Link(
            self.request.route_path(SUPPLIER_ITEM_ROUTE, id=supplier.id),
            "Voir ce fournisseur",
            title="Voir ou modifier ce fournisseur",
            icon="arrow-right",
        )


class SuppliersCsv(SuppliersListTools, BaseCsvView):
    """
    Supplier csv view
    """

    model = Supplier

    @property
    def filename(self):
        return "fournisseurs.csv"

    def query(self):
        company = self.request.context
        query = Supplier.query().options(undefer_group("edit"))
        return query.filter(Supplier.company_id == company.id)


def includeme(config):
    config.add_view(
        SuppliersListView,
        route_name=COMPANY_SUPPLIERS_ROUTE,
        renderer="third_party/supplier/list.mako",
        request_method="GET",
        context=Company,
        permission=PERMISSIONS["company.view"],
    )
    config.add_view(
        CaeSuppliersListView,
        route_name=CAE_SUPPLIERS_ROUTE,
        renderer="third_party/supplier/list.mako",
        request_method="GET",
        permission=PERMISSIONS["global.manage_third_parties"],
    )
    config.add_view(
        SuppliersCsv,
        route_name="suppliers.csv",
        request_method="GET",
        context=Company,
        permission=PERMISSIONS["company.view"],
    )

    config.add_company_menu(
        parent="supply",
        order=0,
        label="Fournisseurs",
        route_name=COMPANY_SUPPLIERS_ROUTE,
        route_id_key="company_id",
        routes_prefixes=["supplier"],
    )

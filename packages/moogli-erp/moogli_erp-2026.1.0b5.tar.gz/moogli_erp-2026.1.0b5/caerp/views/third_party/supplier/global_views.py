import logging
from typing import Iterable

import colander
from pyramid.httpexceptions import HTTPBadRequest, HTTPFound, HTTPNotFound
from sqlalchemy import func, literal_column, or_

from caerp.consts.permissions import PERMISSIONS
from caerp.controllers.third_party.third_party import (
    update_third_parties_from_siren_api,
    update_third_party_accounting,
)
from caerp.forms.third_party.supplier import (
    get_list_schema,
    get_set_global_accounting_schema,
)
from caerp.models.base import DBSESSION
from caerp.models.company import Company
from caerp.models.third_party.supplier import Supplier
from caerp.services.third_party.supplier import (
    get_global_total_supplier_invoice_value,
    get_suppliers_from_siren,
)
from caerp.services.third_party.third_party import (
    CompanyData,
    find_company_infos,
    get_unique_third_party_attribute_by_siren,
)
from caerp.utils.widgets import Link
from caerp.views import BaseFormView, BaseListView, BaseView, TreeMixin
from caerp.views.supply.invoices.routes import (
    COLLECTION_ROUTE as INVOICE_COLLECTION_ROUTE,
)
from caerp.views.supply.orders.routes import COLLECTION_ROUTE as ORDER_COLLECTION_ROUTE

from .routes import (
    GLOBAL_SUPPLIER_ITEM_ROUTE,
    GLOBAL_SUPPLIERS_ROUTE,
    SUPPLIER_ITEM_ROUTE,
)

logger = log = logging.getLogger(__name__)


class GlobalSuppliersListView(BaseListView, TreeMixin):
    title = "Référenciel fournisseur commun de la CAE"
    route_name = GLOBAL_SUPPLIERS_ROUTE

    add_template_vars = (
        "stream_actions",
        "get_item_url",
        "title",
    )
    sort_columns = {
        "siret": Supplier.siret,
        "company_name": Supplier.company_name,
        "last_update": "api_last_update",
        "nb_companies": "nb_companies",
    }
    default_sort = "nb_companies"
    default_direction = "desc"

    def get_schema(self):
        return get_list_schema(is_global=True)

    @property
    def tree_url(self):
        return self.request.route_path(self.route_name)

    def query(self):
        query1 = (
            DBSESSION()
            .query(
                Supplier.id.label("supplier_id"),
                func.substr(Supplier.siret, 1, 9).label("siren"),
                literal_column('"-"').label("siret"),
                Supplier.company_name.label("name"),
                func.min(Supplier.created_at).label("created_at"),
                func.max(Supplier.api_last_update).label("api_last_update"),
                func.count(Supplier.id).label("nb_companies"),
                Company.name.label("company_name"),
                Company.id.label("company_id"),
                Supplier.archived.label("archived"),
            )
            .join(Company, Supplier.company_id == Company.id)
            .filter(Supplier.siret != "")
            .filter(Supplier.type != "internal")
            .group_by("siren")
        )
        query2 = (
            DBSESSION()
            .query(
                Supplier.id.label("supplier_id"),
                literal_column("''").label("siren"),
                Supplier.siret,
                Supplier.company_name.label("name"),
                Supplier.created_at,
                Supplier.api_last_update.label("api_last_update"),
                literal_column("1").label("nb_companies"),
                Company.name.label("company_name"),
                Company.id.label("company_id"),
                Supplier.archived.label("archived"),
            )
            .join(Company, Supplier.company_id == Company.id)
            .filter(Supplier.siret.in_(("", None)))
            .filter(Supplier.type != "internal")
            .filter(Supplier.archived.is_(False))
        )
        return query1.union(query2)

    def filter_search(self, query, appstruct):
        search = appstruct.get("search")
        if search:
            query = query.filter(
                or_(
                    literal_column("company_name").like("%" + search + "%"),
                    literal_column("siret").like("%" + search + "%"),
                )
            )
        return query

    def filter_company_id(self, query, appstruct):
        company_id = appstruct.get("company_id")
        if company_id:
            query = query.filter(literal_column("company_id") == company_id)
        return query

    def filter_archived(self, query, appstruct):
        archived = appstruct.get("archived", False)
        if archived in (False, colander.null):
            query = query.filter(Supplier.archived.is_(False))
        return query

    def stream_actions(self, row):
        yield Link(
            self.get_item_url(row),
            "Voir ce fournisseur",
            title="Voir ou modifier ce fournisseur",
            icon="arrow-right",
        )

    def get_item_url(self, row):
        if row["nb_companies"] == 1 and row["supplier_id"] != 0:
            return self.request.route_path(SUPPLIER_ITEM_ROUTE, id=row["supplier_id"])
        else:
            return self.request.route_path(
                GLOBAL_SUPPLIER_ITEM_ROUTE, siren=row["siren"]
            )

    def __call__(self):
        self.populate_navigation()
        return super().__call__()


class GlobalSupplierView(BaseView, TreeMixin):
    title = "Fournisseur de la CAE"
    route_name = GLOBAL_SUPPLIER_ITEM_ROUTE

    siren = None
    supplier_data = {}

    def __init__(self, context, request=None):
        super().__init__(context, request)
        self.siren = self.request.matchdict["siren"]

    @property
    def tree_url(self):
        return self.request.route_path(self.route_name, siren=self.siren)

    def _get_title(self, supplier_data: CompanyData) -> str:
        return f"Fournisseur de la CAE : {supplier_data.company_name}"

    def _get_supplier_data_from_siren(self, siren) -> dict:
        search_result = find_company_infos(self.request, siren, only_siege=True)
        siren_numbers = set(i.siren for i in search_result)
        if len(siren_numbers) == 1:
            supplier_data = search_result[0]
        else:
            logger.error(
                f"Fournisseur {siren} : Résultats multiples dans l'annuaire SIRENE"
            )
            return None
        suppliers = get_suppliers_from_siren(self.request, siren)
        result = {"supplier_data": supplier_data, "company_suppliers": suppliers}

        compte_cg = set(
            [supplier.compte_cg for supplier in suppliers if supplier.compte_cg]
        )
        compte_tiers = set(
            [supplier.compte_tiers for supplier in suppliers if supplier.compte_tiers]
        )

        if len(compte_cg) == 1:
            result["compte_cg"] = compte_cg.pop()
        elif len(compte_cg) > 1:
            result["compte_cg"] = "multiple"
        else:
            result["compte_cg"] = "Non renseigné"

        if len(compte_tiers) == 1:
            result["compte_tiers"] = compte_tiers.pop()
        elif len(compte_tiers) > 1:
            result["compte_tiers"] = "multiple"
        else:
            result["compte_tiers"] = "Non renseigné"
        return result

    def stream_main_actions(self) -> Iterable:
        # yield POSTButton(
        #     self.request.route_path(
        #         GLOBAL_SUPPLIER_ITEM_ROUTE,
        #         siren=self.siren,
        #         _query={"action": "update_data_from_siren"},
        #     ),
        #     "Mettre à jour depuis l'API",
        #     title=(
        #         "Mettre à jour l'ensemble des fournisseurs avec les données de l'API "
        #         "de l'annuaire SIRENE"
        #     ),
        #     icon="redo-alt",
        # )
        yield Link(
            self.request.route_path(
                GLOBAL_SUPPLIER_ITEM_ROUTE,
                siren=self.siren,
                _query={"action": "set_accounting"},
            ),
            "Modifier les comptes comptables",
            title=(
                "Modifier les comptes comptables et tiers pour l'ensemble"
                " des fournisseurs correspondant"
            ),
            icon="pen",
        )

    def stream_more_actions(self):
        yield Link(
            self.request.route_path(
                INVOICE_COLLECTION_ROUTE,
                _query={
                    "siret": self.siren,
                    "__formid__": "deform",
                    "submit": "submit",
                },
            ),
            "Factures",
            title="Voir les factures fournisseur associées à ce fournisseur",
            icon="list-alt",
        )
        yield Link(
            self.request.route_path(
                ORDER_COLLECTION_ROUTE,
                _query={
                    "siret": self.siren,
                    "__formid__": "deform",
                    "submit": "submit",
                },
            ),
            "Commandes",
            title="Voir les commandes fournisseur associées à ce fournisseur",
            icon="list-alt",
        )

    def stream_col_actions(self, supplier: Supplier) -> Iterable:
        yield Link(
            self.request.route_path(
                SUPPLIER_ITEM_ROUTE,
                id=supplier.id,
            ),
            "Voir la fiche de ce fournisseur",
            title=(
                f"Voir la fiche du fournisseur {supplier.name} de "
                f"l'enseigne {supplier.company.name}"
            ),
            icon="arrow-right",
        )

    def get_row_total_ht(self, supplier: Supplier) -> float:
        return get_global_total_supplier_invoice_value(
            self.request, supplier_id=supplier.id
        )

    def __call__(self) -> dict:
        self.populate_navigation()
        result = self._get_supplier_data_from_siren(self.siren)
        if result is None:
            raise HTTPNotFound()
        self._get_title(result["supplier_data"])
        result["title"] = self.title
        result["stream_main_actions"] = self.stream_main_actions
        result["stream_more_actions"] = self.stream_more_actions
        result["stream_col_actions"] = self.stream_col_actions
        result["total_invoiced"] = get_global_total_supplier_invoice_value(
            self.request, self.siren
        )
        result["get_row_total_ht"] = self.get_row_total_ht
        return result


def update_supplier_data_from_siren(request):
    """
    Met à jour l'ensemble des instances Supplier associées à un
    même fournisseur avec les données de l'api de l'annuaire SIRENE
    """
    siren = request.matchdict["siren"]
    try:
        update_third_parties_from_siren_api(request, siren)
        request.session.flash("Les données des fournisseurs ont bien été mises à jour.")
    except Exception as e:
        request.session.flash(f"Erreur lors de la mise à jour des fournisseurs : {e}")
    return HTTPFound(request.route_path(GLOBAL_SUPPLIER_ITEM_ROUTE, siren=siren))


class UpdateSupplierAccountingView(BaseFormView, TreeMixin):
    title = "Modifier les comptes comptables et tiers"
    add_template_vars = ("help_message",)
    help_message = (
        """Les comptes comptables et tiers seront modifiés pour tous les fournisseurs"""
    )
    success_message = (
        "Les comptes comptables et tiers ont bien été modifiés pour "
        "tous les fournisseurs correspondant."
    )

    def get_schema(self):
        return get_set_global_accounting_schema()

    def before(self, form):
        siren = self.request.matchdict["siren"]
        appstruct = {}
        compte_cg = get_unique_third_party_attribute_by_siren(
            self.request, siren, "compte_cg"
        )
        if compte_cg is not None:
            appstruct["compte_cg"] = compte_cg
        compte_tiers = get_unique_third_party_attribute_by_siren(
            self.request, siren, "compte_tiers"
        )
        if compte_tiers is not None:
            appstruct["compte_tiers"] = compte_tiers
        form.set_appstruct(appstruct)

    def submit_success(self, appstruct):
        siren = self.request.matchdict["siren"]
        compte_cg = appstruct.get("compte_cg")
        compte_tiers = appstruct.get("compte_tiers")
        if not siren:
            raise HTTPBadRequest("Aucun SIREN fourni")
        update_third_party_accounting(self.request, siren, compte_cg, compte_tiers)
        self.request.session.flash(self.success_message)
        return HTTPFound(
            self.request.route_path(
                GLOBAL_SUPPLIER_ITEM_ROUTE,
                siren=siren,
            )
        )

    def __call__(self):
        self.populate_navigation()
        return super().__call__()


def includeme(config):
    config.add_tree_view(
        GlobalSuppliersListView,
        route_name=GLOBAL_SUPPLIERS_ROUTE,
        renderer="third_party/supplier/global_list.mako",
        permission=PERMISSIONS["global.manage_third_parties"],
    )

    config.add_tree_view(
        GlobalSupplierView,
        parent=GlobalSuppliersListView,
        renderer="third_party/supplier/global_item.mako",
        permission=PERMISSIONS["global.manage_third_parties"],
    )
    config.add_view(
        update_supplier_data_from_siren,
        route_name=GLOBAL_SUPPLIER_ITEM_ROUTE,
        request_method="POST",
        request_param="action=update_data_from_siren",
        permission=PERMISSIONS["global.manage_third_parties"],
    )
    config.add_tree_view(
        UpdateSupplierAccountingView,
        parent=GlobalSupplierView,
        route_name=GLOBAL_SUPPLIER_ITEM_ROUTE,
        request_param="action=set_accounting",
        permission=PERMISSIONS["global.manage_third_parties"],
        renderer="base/formpage.mako",
    )

    config.add_admin_menu(
        parent="supply",
        order=0,
        label="Fournisseurs",
        href=GLOBAL_SUPPLIERS_ROUTE,
        permission=PERMISSIONS["global.manage_third_parties"],
    )

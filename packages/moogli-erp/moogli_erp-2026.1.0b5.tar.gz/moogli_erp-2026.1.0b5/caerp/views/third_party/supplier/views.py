import logging
from typing import Dict

from pyramid.httpexceptions import HTTPFound

from caerp.consts.permissions import PERMISSIONS
from caerp.models.company import Company
from caerp.models.third_party.supplier import Supplier
from caerp.resources import node_view_only_js
from caerp.utils.rest.apiv1 import make_redirect_view
from caerp.utils.widgets import Link, POSTButton
from caerp.views import BaseFormView, BaseView, JsAppViewMixin, TreeMixin
from caerp.views.csv_import import ConfigFieldAssociationView, CsvFileUploadView
from caerp.views.third_party.supplier.lists import SuppliersListView

from .controller import SupplierAddEditController
from .routes import (
    COMPANY_SUPPLIERS_ADD_ROUTE,
    COMPANY_SUPPLIERS_API_ROUTE,
    SUPPLIER_ITEM_ROUTE,
)

logger = log = logging.getLogger(__name__)


def get_supplier_url(
    request,
    supplier=None,
    _query={},
    suffix="",
    api=False,
    _anchor=None,
    absolute=False,
):
    if supplier is None:
        supplier = request.context

    # La route pour le client est toujours nommée "supplier" et non
    #  "/suppliers/{id}"
    if not suffix and not api:
        route = SUPPLIER_ITEM_ROUTE
    else:
        # On est donc obligé de traiter le cas où on veut construire d'autres route
        # dynamiquement à part
        route = SUPPLIER_ITEM_ROUTE

    if suffix:
        route += suffix

    if api:
        route = "/api/v1%s" % route

    params = dict(id=supplier.id, _query=_query)
    if _anchor is not None:
        params["_anchor"] = _anchor

    if absolute:
        method = request.route_url
    else:
        method = request.route_path
    return method(route, **params)


def supplier_archive(request):
    """
    Archive the current supplier
    """
    supplier = request.context
    if not supplier.archived:
        supplier.archived = True
    else:
        supplier.archived = False
    request.dbsession.merge(supplier)
    return HTTPFound(request.referer)


def supplier_delete(request):
    """
    Delete the current supplier
    """
    supplier = request.context
    request.dbsession.delete(supplier)
    request.session.flash(
        "Le fournisseur '{0}' a bien été supprimé".format(supplier.label)
    )
    return HTTPFound(request.referer)


class BaseSupplierView(BaseFormView, JsAppViewMixin, TreeMixin):
    """
    Return the view of a supplier
    """

    route_name = SUPPLIER_ITEM_ROUTE

    @property
    def tree_url(self):
        return self.request.route_path(self.route_name, id=self.context.id)

    @property
    def title(self):
        return f"Fournisseur : {self.context.label}"

    def _get_more_actions(self):
        """
        Collect available buttons that will be displayed in the upper left
        corner of the screen

        :rtype: list
        """
        return [
            Link(
                self.request.route_path(
                    SUPPLIER_ITEM_ROUTE, id=self.context.id, _query=dict(action="edit")
                ),
                "Modifier",
                icon="pen",
                css="btn icon",
            ),
        ]

    def _get_main_actions(self):
        """
        Collect available buttons that will be displayed in the upper right
        corner of the screen

        :rtype: list
        """
        result = []
        pending_orders = self.context.get_orders(
            pending_invoice_only=True, internal=False
        )
        pending_orders_ids = [i.id for i in pending_orders]

        if pending_orders_ids:
            result.append(
                POSTButton(
                    self.request.route_path(
                        "/companies/{id}/supplier_invoices",
                        id=self.context.company_id,
                        _query=dict(action="new"),
                    ),
                    'Facturer<span class="no_mobile">&nbsp;les encours validés'
                    "</span>",
                    icon="file-invoice-euro",
                    css="btn btn-primary icon",
                    extra_fields=[
                        ("supplier_orders_ids", pending_orders_ids),
                        ("submit", ""),
                    ],
                    title="Facturer les encours validés",
                )
            )
        if not self.context.is_internal():
            result.append(
                POSTButton(
                    self.request.route_path(
                        "/companies/{id}/supplier_orders",
                        id=self.context.company_id,
                        _query=dict(action="new"),
                    ),
                    '<span class="screen-reader-text">Nouvelle </span>' "Commande",
                    icon="plus",
                    css="btn btn-primary icon",
                    extra_fields=[
                        ("supplier_id", self.context.id),
                        ("submit", ""),
                    ],
                    title="Nouvelle commande",
                )
            )
            result.append(
                POSTButton(
                    self.request.route_path(
                        "/companies/{id}/supplier_invoices",
                        id=self.context.company_id,
                        _query=dict(action="new"),
                    ),
                    '<span class="screen-reader-text">Nouvelle </span>' "Facture",
                    icon="plus",
                    css="btn icon",
                    extra_fields=[
                        ("supplier_id", self.context.id),
                        ("submit", ""),
                    ],
                    title="Nouvelle facture",
                )
            )
        return result

    def context_url(self, _query: Dict[str, str] = {}):
        return self.request.route_url(
            "/api/v1/suppliers/{id}", id=self.context.id, _query=_query
        )

    def __call__(self):
        self.populate_navigation()
        # TODO Fil d'ariane NOK (liste des frns jamais présente)
        node_view_only_js.need()
        return dict(
            title=self.title,
            supplier=self.request.context,
            main_actions=self._get_main_actions(),
            more_actions=self._get_more_actions(),
            records=self.get_subview_records(),
            js_app_options=self.get_js_app_options(),
        )

    def get_subview_records(self):
        """
        Returns a list of items to show additionaly to the main view.
        """
        raise NotImplementedError()


class SupplierViewRunningOrders(BaseSupplierView):
    """Supplier detail with running orders tab opened"""

    def get_subview_records(self):
        from caerp.models.supply import SupplierOrder

        query = self.context.get_orders(waiting_only=True)
        query = query.order_by(-SupplierOrder.created_at)
        return query


class SupplierViewInvoicedOrders(BaseSupplierView):
    """Supplier detail with invoiced orders tab opened"""

    def get_subview_records(self):
        from caerp.models.supply import SupplierOrder

        query = self.context.get_orders(invoiced_only=True)
        query = query.order_by(-SupplierOrder.created_at)
        return query


class SupplierViewExpenseLines(BaseSupplierView):
    def get_subview_records(self):
        query = self.context.get_expenselines()
        return query


class SupplierViewInvoices(BaseSupplierView):
    """Supplier detail with invoices tab opened"""

    def get_subview_records(self):
        from caerp.models.supply import SupplierInvoice

        query = self.context.get_invoices()
        query = query.order_by(-SupplierInvoice.date)
        return query


class SupplierAddView(BaseView, JsAppViewMixin, TreeMixin):
    title = "Ajouter un fournisseur"
    controller_class = SupplierAddEditController
    edit = False
    route_name = COMPANY_SUPPLIERS_ADD_ROUTE

    def __init__(self, context, request=None):
        super().__init__(context, request)
        self.controller = self.controller_class(self.request, edit=self.edit)

    def context_url(self, _query={}):
        return self.request.route_path(
            COMPANY_SUPPLIERS_API_ROUTE, id=self.context.id, _query=_query
        )

    def more_js_app_options(self):
        result = super().more_js_app_options()
        result["context_type"] = "supplier"
        return result

    def __call__(self) -> dict:
        from caerp.resources import third_party_js

        third_party_js.need()
        self.populate_navigation()

        result = {
            "title": self.title,
            "js_app_options": self.get_js_app_options(),
        }
        return result


class SupplierEditView(SupplierAddView, TreeMixin):
    controller_class = SupplierAddEditController
    edit = True
    route_name = SUPPLIER_ITEM_ROUTE

    @property
    def title(self):
        return "Modifier le fournisseur '{0}' de l'enseigne '{1}'".format(
            self.context.name, self.context.company.name
        )

    def context_url(self, _query={}):
        return get_supplier_url(self.request, api=True, _query=_query)

    def more_js_app_options(self):
        result = super().more_js_app_options()
        result["third_party_id"] = self.context.id
        return result


class SupplierImportStep1(CsvFileUploadView):
    title = "Import des fournisseurs, étape 1 : chargement d'un fichier au \
format csv"
    model_types = ("suppliers",)
    default_model_type = "suppliers"

    def get_next_step_route(self, args):
        return self.request.route_path(
            "company_suppliers_import_step2", id=self.context.id, _query=args
        )


class SupplierImportStep2(ConfigFieldAssociationView):
    title = "Import de fournisseurs, étape 2 : associer les champs"
    model_types = SupplierImportStep1.model_types

    def get_previous_step_route(self):
        return self.request.route_path(
            "company_suppliers_import_step1",
            id=self.context.id,
        )

    def get_default_values(self):
        log.info("Asking for default values : %s" % self.context.id)
        return dict(company_id=self.context.id)


def includeme(config):
    config.add_tree_view(
        SupplierAddView,
        parent=SuppliersListView,
        renderer="base/vue_app.mako",
        layout="vue_opa",
        context=Company,
        permission=PERMISSIONS["context.add_supplier"],
    )
    config.add_tree_view(
        SupplierEditView,
        parent=BaseSupplierView,
        renderer="base/vue_app.mako",
        request_param="action=edit",
        layout="vue_opa",
        context=Supplier,
        permission=PERMISSIONS["context.edit_supplier"],
    )
    config.add_tree_view(
        make_redirect_view("supplier_running_orders", True),
        route_name=SUPPLIER_ITEM_ROUTE,
        request_method="GET",
        permission=PERMISSIONS["company.view"],
        context=Supplier,
    )
    config.add_tree_view(
        SupplierViewRunningOrders,
        parent=SuppliersListView,
        route_name="supplier_running_orders",
        renderer="/third_party/supplier/running_orders.mako",
        request_method="GET",
        permission=PERMISSIONS["company.view"],
        layout="supplier",
        context=Supplier,
    )
    config.add_tree_view(
        SupplierViewInvoicedOrders,
        parent=SuppliersListView,
        route_name="supplier_invoiced_orders",
        renderer="/third_party/supplier/invoiced_orders.mako",
        request_method="GET",
        permission=PERMISSIONS["company.view"],
        layout="supplier",
        context=Supplier,
    )
    config.add_tree_view(
        SupplierViewInvoices,
        parent=SuppliersListView,
        route_name="supplier_invoices",
        renderer="/third_party/supplier/invoices.mako",
        request_method="GET",
        permission=PERMISSIONS["company.view"],
        layout="supplier",
        context=Supplier,
    )
    config.add_tree_view(
        SupplierViewExpenseLines,
        parent=SuppliersListView,
        route_name="supplier_expenselines",
        renderer="/third_party/supplier/expenses.mako",
        request_method="GET",
        permission=PERMISSIONS["company.view"],
        layout="supplier",
        context=Supplier,
    )
    config.add_view(
        supplier_delete,
        route_name=SUPPLIER_ITEM_ROUTE,
        request_param="action=delete",
        permission=PERMISSIONS["context.delete_supplier"],
        request_method="POST",
        require_csrf=True,
        context=Supplier,
    )
    config.add_view(
        supplier_archive,
        route_name=SUPPLIER_ITEM_ROUTE,
        request_param="action=archive",
        permission=PERMISSIONS["context.edit_supplier"],
        request_method="POST",
        require_csrf=True,
        context=Supplier,
    )
    config.add_view(
        SupplierImportStep1,
        route_name="company_suppliers_import_step1",
        permission=PERMISSIONS["context.add_supplier"],
        renderer="base/formpage.mako",
        context=Company,
    )
    config.add_view(
        SupplierImportStep2,
        route_name="company_suppliers_import_step2",
        permission=PERMISSIONS["context.add_supplier"],
        renderer="base/formpage.mako",
        context=Company,
    )

from typing import Dict, List

from caerp.consts.civilite import CIVILITE_OPTIONS
from caerp.consts.permissions import PERMISSIONS
from caerp.forms.jsonschema import convert_to_jsonschema
from caerp.forms.third_party.supplier import (
    get_company_supplier_schema,
    get_internal_supplier_schema,
)
from caerp.models.company import Company
from caerp.models.status import StatusLogEntry
from caerp.models.third_party import Supplier
from caerp.views import BaseRestView
from caerp.views.status.rest_api import StatusLogEntryRestView
from caerp.views.status.utils import get_visibility_options
from caerp.views.third_party.supplier.routes import (
    COMPANY_SUPPLIERS_API_ROUTE,
    SUPPLIER_ITEM_API_ROUTE,
    SUPPLIER_ITEM_STATUSLOGENTRY_API_ROUTE,
    SUPPLIER_STATUSLOGENTRY_ITEM_API_ROUTE,
)


class SupplierRestView(BaseRestView):
    """
    Supplier rest view

    collection : context Root

        GET : return list of suppliers (company_id should be provided)
    """

    edit = False

    def __init__(self, context, request=None):
        super().__init__(context, request)
        self.edit = isinstance(context, Supplier)

    def get_schema(self, submitted):
        if isinstance(self.context, Supplier):
            if self.context.is_internal():
                return get_internal_supplier_schema(edit=True)
        return get_company_supplier_schema()

    def collection_get(self):
        return self.context.suppliers

    def post_format(self, entry, edit, attributes):
        """
        Associate a newly created element to the parent company
        """
        if not edit:
            entry.company = self.context
        # TODO Mettre à jour tous les tiers avec le même SIREN à l'enregistrement
        return entry

    def civilite_options(self) -> List[Dict]:
        return [{"id": c[0], "label": c[1]} for c in CIVILITE_OPTIONS]

    def form_config(self):
        schemas = {
            "company": get_company_supplier_schema().bind(request=self.request),
            "internal": get_internal_supplier_schema(edit=True).bind(
                request=self.request
            ),
        }
        for key, schema in schemas.items():
            schemas[key] = convert_to_jsonschema(schema)

        if isinstance(self.context, Company):
            company_id = self.context.id
        else:
            company_id = self.context.company_id

        return {
            "options": {
                "visibilities": get_visibility_options(self.request),
                "civilite_options": self.civilite_options(),
                "is_admin": self.request.has_permission(
                    PERMISSIONS["global.manage_accounting"]
                ),
                "address_completion": False,
                "company_id": company_id,
                "edit": self.edit,
                "context_type": "supplier",
            },
            "schemas": schemas,
        }


def includeme(config):
    config.add_rest_service(
        SupplierRestView,
        SUPPLIER_ITEM_API_ROUTE,
        collection_route_name=COMPANY_SUPPLIERS_API_ROUTE,
        collection_context=Company,
        context=Supplier,
        collection_view_rights=PERMISSIONS["company.view"],
        view_rights=PERMISSIONS["company.view"],
        edit_rights=PERMISSIONS["context.edit_supplier"],
        add_rights=PERMISSIONS["context.add_supplier"],
        delete_rights=PERMISSIONS["context.delete_supplier"],
    )

    # Form config for customer add/edit
    for route, perm, context in (
        (SUPPLIER_ITEM_API_ROUTE, "context.edit_supplier", Supplier),
        (COMPANY_SUPPLIERS_API_ROUTE, "context.add_supplier", Company),
    ):
        config.add_view(
            SupplierRestView,
            attr="form_config",
            route_name=route,
            renderer="json",
            request_param="form_config",
            context=context,
            permission=PERMISSIONS[perm],
        )

    config.add_rest_service(
        StatusLogEntryRestView,
        SUPPLIER_STATUSLOGENTRY_ITEM_API_ROUTE,
        collection_route_name=SUPPLIER_ITEM_STATUSLOGENTRY_API_ROUTE,
        collection_view_rights=PERMISSIONS["company.view"],
        context=StatusLogEntry,
        add_rights=PERMISSIONS["company.view"],
        view_rights=PERMISSIONS["context.view_statuslogentry"],
        edit_rights=PERMISSIONS["context.edit_statuslogentry"],
        delete_rights=PERMISSIONS["context.delete_statuslogentry"],
    )

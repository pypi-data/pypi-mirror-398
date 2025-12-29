import logging
import os

from caerp.consts.permissions import PERMISSIONS
from caerp.forms.admin import get_config_schema
from caerp.views.admin.tools import BaseConfigView

from . import SALE_URL, SaleIndexView

logger = logging.getLogger(__name__)


FORM_CONFIG_URL = os.path.join(SALE_URL, "internal_invoicing")


class InternalInvoicingAdminView(BaseConfigView):
    title = "Facturation interne"
    description = "Gestion du cycle de facturation interne"
    route_name = FORM_CONFIG_URL
    validation_msg = "Les informations ont bien été enregistrées"

    keys = ("internal_invoicing_active",)
    schema = get_config_schema(keys)
    permission = PERMISSIONS["global.config_sale"]


def includeme(config):
    view = InternalInvoicingAdminView
    config.add_route(view.route_name, view.route_name)
    config.add_admin_view(view, parent=SaleIndexView)

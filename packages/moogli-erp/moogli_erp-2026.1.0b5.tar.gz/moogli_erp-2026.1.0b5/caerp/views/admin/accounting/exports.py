import logging
import os

from caerp.consts.permissions import PERMISSIONS
from caerp.forms.admin import get_config_schema
from caerp.views.admin.accounting import ACCOUNTING_URL, AccountingIndexView
from caerp.views.admin.tools import BaseConfigView

logger = logging.getLogger(__name__)


BASE_URL = os.path.join(ACCOUNTING_URL, "accounting_exports")


class AccountingExportsView(BaseConfigView):
    title = "Exports comptables"
    description = "Configurer les paramètres des exports comptables."
    route_name = BASE_URL

    validation_msg = "Les informations ont bien été enregistrées"
    keys = (
        "thirdparty_account_mandatory_user",
        "thirdparty_account_mandatory_customer",
        "thirdparty_account_mandatory_supplier",
    )
    schema = get_config_schema(keys)
    permission = PERMISSIONS["global.config_accounting"]


def add_routes(config):
    """
    Add the routes related to the current module
    """
    config.add_route(BASE_URL, BASE_URL)


def add_views(config):
    """
    Add views defined in this module
    """
    config.add_admin_view(
        AccountingExportsView,
        parent=AccountingIndexView,
    )


def includeme(config):
    add_routes(config)
    add_views(config)

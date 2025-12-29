import logging
import os

from caerp.consts.permissions import PERMISSIONS
from caerp.forms.admin import get_config_schema
from caerp.views.admin.accounting import ACCOUNTING_URL, AccountingIndexView
from caerp.views.admin.tools import BaseConfigView

logger = logging.getLogger(__name__)


BASE_URL = os.path.join(ACCOUNTING_URL, "accounting_software")


class AccountingSoftwareView(BaseConfigView):
    title = "Logiciel de comptabilité"
    description = "Configurer les informations concernant le logiciel de comptabilité."
    route_name = BASE_URL

    validation_msg = "Les informations ont bien été enregistrées"
    keys = ("accounting_software", "accounting_label_maxlength")
    schema = get_config_schema(keys)
    permission = PERMISSIONS["global.config_accounting"]


def includeme(config):
    config.add_route(BASE_URL, BASE_URL)
    config.add_admin_view(
        AccountingSoftwareView,
        parent=AccountingIndexView,
    )

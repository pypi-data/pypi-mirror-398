"""
RGPD Related Tasks

1- Collect the data to be cleaned
2- Build the Email
3- 
"""
import logging

import transaction
from pyramid_celery import celery_app

from caerp.celery.conf import get_request, get_sysadmin_mail
from caerp.celery.mail import (
    send_rgpd_customer_notification,
    send_rgpd_userdata_notification,
    send_unused_login_notification,
)
from caerp.consts.rgpd import (
    RGPD_DEFAULT_CUSTOMER_RETENTION_DAYS,
    RGPD_DEFAULT_LOGIN_RETENTION_DAYS,
    RGPD_DEFAULT_USERDATA_RETENTION_DAYS,
)
from caerp.models.config import Config
from caerp.services.rgpd.customer import get_customers_not_used_for
from caerp.services.rgpd.user import (
    get_accounts_not_used_for,
    get_userdatas_not_used_for,
)
from caerp.services.rgpd.utils import get_retention_days

logger = logging.getLogger(__name__)


def get_rgpd_email(request):
    return Config.get_value("rgpd_manager_email", default=None, type_=str)


@celery_app.task
def check_rgpd_userdata():
    logger.debug("# RGPD : Check Userdata")
    request = get_request()
    email = get_rgpd_email(request)
    if email is None:
        logger.debug("# RGPD : Aucun responsable RGPD configuré")
        return
    else:
        recipients = [email, get_sysadmin_mail()]
    try:
        request = get_request()
        retention_days = get_retention_days(
            request, "userdata", RGPD_DEFAULT_USERDATA_RETENTION_DAYS
        )
        entries = get_userdatas_not_used_for(request, retention_days)
        if len(entries) > 0:
            logger.debug("# {} entrées à nettoyer".format(len(entries)))
            logger.debug("# Envoi d'un mail au responsable")
            send_rgpd_userdata_notification(
                request, recipients, entries, retention_days
            )
    except Exception:
        logger.exception("Erreur lors de la vérification des données de GS à nettoyer")
        transaction.abort()


@celery_app.task
def check_unused_logins():
    logger.debug("# RGPD : Check Unused Logins")
    request = get_request()
    email = get_rgpd_email(request)
    if email is None:
        logger.debug("# RGPD : Aucun responsable RGPD configuré")
        return
    else:
        recipients = [email, get_sysadmin_mail()]
    try:
        request = get_request()
        retention_days = get_retention_days(
            request, "login", RGPD_DEFAULT_LOGIN_RETENTION_DAYS
        )
        entries = get_accounts_not_used_for(request, retention_days)
        if len(entries) > 0:
            logger.debug("# {} entrées à nettoyer".format(len(entries)))
            logger.debug("# Envoi d'un mail au responsable")
            send_unused_login_notification(request, recipients, entries, retention_days)
    except Exception:
        logger.exception("Erreur lors de la vérification des comptes à nettoyer")
        transaction.abort()


@celery_app.task
def check_rgpd_customers():
    logger.debug("# RGPD : Check Customers")
    request = get_request()
    email = get_rgpd_email(request)
    if email is None:
        logger.debug("# RGPD : Aucun responsable RGPD configuré")
        return
    else:
        recipients = [email, get_sysadmin_mail()]
    try:
        request = get_request()
        retention_days = get_retention_days(
            request, "customer", RGPD_DEFAULT_CUSTOMER_RETENTION_DAYS
        )
        entries = get_customers_not_used_for(request, retention_days)
        if len(entries) > 0:
            logger.debug("# {} entrées à nettoyer".format(len(entries)))
            logger.debug("# Envoi d'un mail au responsable")
            send_rgpd_customer_notification(
                request, recipients, entries, retention_days
            )
    except Exception:
        logger.exception("Erreur lors de la vérification des données client à nettoyer")
        transaction.abort()

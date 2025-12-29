# -*- coding: utf-8 -*-
"""
Configuration management tools

Tools to retrieve elements from the main app configuration
"""
from caerp.models.config import get_admin_mail


def get_registry():
    """
    Return the Pyramid application registry associated to the current running
    application

    :returns: A Pyramid registry instance
    """
    from pyramid_celery import celery_app

    return celery_app.conf["PYRAMID_REGISTRY"]


def get_request():
    """
    Return the Pyramid application request associated to the current running
    application context
    """
    from pyramid_celery import celery_app

    return celery_app.conf["PYRAMID_REQUEST"]


def get_setting(key, mandatory=False, default=None):
    """
    Collect a given setting

    :param str key: The key to collect
    :param bool mandatory: Is the key mandatory (if it is a KeyError may be
    raised)
    :param default: The default value to return
    :rtype: str
    """
    settings = get_registry().settings
    if mandatory:
        return settings[key]
    else:
        return settings.get(key, default)


def get_sysadmin_mail():
    """
    Retrieve the sysadmin mail from the current configuration or None if not set

    :rtype: str
    """
    return get_setting("caerp.sysadmin_mail")


def get_recipients_addresses(request):
    """
    Retrieve recipients mail adresses
    :param obj request: The request object
    :returns: A list of mail adresses
    """
    _admin_mail = get_admin_mail()
    _sysadmin_mail = get_sysadmin_mail()
    mail_addresses = []
    if _admin_mail:
        mail_addresses.append(_admin_mail)
    if _sysadmin_mail:
        mail_addresses.append(_sysadmin_mail)

    if mail_addresses:
        setattr(request, "registry", get_registry())
    return mail_addresses

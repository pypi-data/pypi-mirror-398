import locale

# flake8: noqa: E402

locale.setlocale(locale.LC_ALL, "fr_FR.UTF-8")
locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")

import logging

from pyramid.paster import setup_logging
from pyramid.path import DottedNameResolver
from pyramid_beaker import set_cache_regions_from_settings

from .interfaces import IAccountingFileParser, IAccountingOperationProducer


def configure_accounting_parser_service(config, settings):
    """
    Configure the service used to parse the accounting operations file (Grand livre)

    factory = request.find_service_factory(IAccountingFileParser)
    parser = factory(filepath, request)

    """
    for interface, default_module_path, setting_key in (
        (
            IAccountingFileParser,
            "caerp.celery.parsers.sage.parser_factory",
            "caerp.celery.interfaces.IAccountingFileParser",
        ),
        (
            IAccountingOperationProducer,
            "caerp.celery.parsers.sage.producer_factory",
            "caerp.celery.interfaces.IAccountingOperationProducer",
        ),
    ):
        if setting_key in settings:
            module_path = settings[setting_key]
        else:
            module_path = default_module_path

        service = DottedNameResolver().resolve(module_path)
        config.register_service_factory(service, interface)


def register_import_model(
    config, key, model, label, permission, excludes, callbacks=()
):
    """
    Register a model for import

    :param obj config: The pyramid configuration object
    :param str key: The key used to identify the model type
    :param class model: The model to be used
    :param str label: A label describing the type of datas
    :param str permission: The permission to associate to this import
    :param tuple excludes: The field of the model we don't want to handle in
    the import
    :param list callbacks: List of callables called after import action
    """

    from caerp.celery.tasks.csv_import import (
        MODELS_CONFIGURATION as IMPORT_MODELS_CONFIGURATION,
    )

    IMPORT_MODELS_CONFIGURATION[key] = {
        "factory": model,
        "label": label,
        "permission": permission,
        "excludes": excludes,
        "callbacks": callbacks,
    }


def register_export_model(config, key, model, options={}):
    """
    Register a model for export

    :param obj config: The pyramid configuration object
    :param str key: The key used to identify the model type
    :param class model: The model to be used
    """
    from caerp.celery.tasks.export import (
        MODELS_CONFIGURATION as EXPORT_MODELS_CONFIGURATION,
    )

    EXPORT_MODELS_CONFIGURATION[key] = {"factory": model}
    EXPORT_MODELS_CONFIGURATION[key].update(options)


def includeme(config):
    """
    Includes some celery specific stuff in the main application
    """
    settings = config.get_settings()
    configure_accounting_parser_service(config, settings)
    config.add_directive("register_import_model", register_import_model)
    config.add_directive("register_export_model", register_export_model)
    config.include("caerp.views.invoices.routes")
    config.include("caerp.celery.tasks")


def worker(global_config, **settings):
    """
    Entry point for the pyramid celery stuff
    """
    logging.basicConfig()
    setup_logging(global_config["__file__"])
    logger = logging.getLogger("caerp")
    logger.debug("Starting celery worker")
    from caerp import (
        configure_filedepot,
        prepare_config,
        prepare_view_config,
        setup_bdd,
    )

    logger.info("Bootstraping app")

    # config.include('pyramid_celery')
    config = prepare_config(**settings)
    dbsession = setup_bdd(settings)
    includeme(config)
    set_cache_regions_from_settings(settings)

    config.configure_celery(global_config["__file__"])
    config.commit()
    config = prepare_view_config(config, dbsession, from_tests=False, **settings)
    configure_filedepot(settings)
    config.include("caerp.views.files")
    return config.make_wsgi_app()


def scheduler(global_config, **settings):
    logging.basicConfig()
    setup_logging(global_config["__file__"])
    logger = logging.getLogger(__name__)
    logger.info("Bootstraping celery scheduler application")
    from caerp import prepare_config

    config = prepare_config(**settings)
    config.include("pyramid_celery")
    config.configure_celery(global_config["__file__"])
    config.commit()
    return config.make_wsgi_app()

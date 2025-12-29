import functools

from sqlalchemy import desc, func

from caerp.compute.math_utils import integer_to_amount, translate_integer_precision
from caerp.consts.permissions import PERMISSIONS
from caerp.models.accounting.bookeeping import CustomInvoiceBookEntryModule
from caerp.models.accounting.operations import AccountingOperation
from caerp.models.supply import InternalSupplierInvoice, SupplierInvoice
from caerp.models.task import Task
from caerp.models.third_party.customer import Customer
from caerp.models.third_party.supplier import Supplier
from caerp.models.tva import Tva
from caerp.models.user.userdatas import UserDatas
from caerp.utils.renderer import configure_export
from caerp.utils.strings import format_supplier_invoice_status


def _add_userdatas_custom_headers(writer, query):
    """
    Specific to userdatas exports

    Add custom headers that are not added through automation

    Add headers for code_compta
    """
    from caerp.models.base import DBSESSION
    from caerp.models.user.user import COMPANY_EMPLOYEE

    # Compte analytique
    query = DBSESSION().query(func.count(COMPANY_EMPLOYEE.c.company_id).label("nb"))
    query = query.group_by(COMPANY_EMPLOYEE.c.account_id)
    code_compta_count = query.order_by(desc("nb")).first()
    if code_compta_count:
        code_compta_count = code_compta_count[0]
        for index in range(0, code_compta_count):
            new_header = {
                "label": "Compte_analytique {0}".format(index + 1),
                "name": "code_compta_{0}".format(index + 1),
            }
            writer.add_extra_header(new_header)

    return writer


def _add_userdatas_code_compta(writer, userdatas):
    """
    Add code compta to exports (specific for userdatas exports)

    :param obj writer: The tabbed file writer
    :param obj userdatas: The UserDatas instance we manage
    """
    user_account = userdatas.user
    if user_account:
        datas = []
        for company in user_account.companies:
            datas.append(company.code_compta)
        writer.add_extra_datas(datas)
    return writer


def _add_invoice_custom_headers(writer, query):
    """
    Invoice export headers
    """
    writer = _add_task_custom_headers(writer, query, topay=True)
    writer.add_extra_header({"label": "Date de début", "name": "start_date"})
    writer.add_extra_header({"label": "Date de fin", "name": "end_date"})
    return writer


def _add_estimation_custom_headers(writer, query):
    """
    Estimation export headers
    """
    return _add_task_custom_headers(writer, query, topay=False)


def _add_task_custom_headers(writer, query, topay):
    writer.add_extra_header({"label": "Montant HT", "name": "ht"})
    writer.add_extra_header({"label": "Montant TTC", "name": "ttc"})
    if topay:
        writer.add_extra_header({"label": "Montant restant dû", "name": "topay"})
    for tva in Tva.query():
        writer.add_extra_header(
            {
                "label": "HT {tva.name}".format(tva=tva),
                "name": "HT {tva.value}".format(tva=tva),
            }
        )
        writer.add_extra_header({"label": tva.name, "name": tva.value})

    writer.add_extra_header({"label": "Assurance", "name": "insurance_label"})
    writer.add_extra_header({"label": "Taux d'assurance", "name": "insurance_rate"})
    writer.add_extra_header(
        {"label": "Montant de l'assurance", "name": "insurance_amount"}
    )
    return writer


def _add_invoice_datas(writer, invoice):
    _has_insurance_module = False
    if CustomInvoiceBookEntryModule.get_by_name("insurance", invoice.prefix):
        _has_insurance_module = True

    ht_values = invoice.tva_ht_parts()
    tva_values = invoice.get_tvas()
    datas = []
    datas.append(integer_to_amount(invoice.ht, precision=5))
    datas.append(integer_to_amount(invoice.ttc, precision=5))
    if hasattr(invoice, "topay") and not invoice.paid_status == "resulted":
        datas.append(integer_to_amount(invoice.topay(), precision=5))
    else:
        datas.append(0)
    for tva in Tva.query():
        datas.append(integer_to_amount(ht_values.get(tva, 0), precision=5))
        datas.append(integer_to_amount(tva_values.get(tva, 0), precision=5))

    if invoice.insurance:
        datas.append(invoice.insurance.label)
    else:
        if not _has_insurance_module:
            datas.append("")
        else:
            level = invoice.get_rate_level("insurance")
            if level == "cae":
                datas.append("Taux de la CAE (module assurance)")
            elif level == "company":
                datas.append("Taux d'assurance de l'enseigne")
            else:
                datas.append("")

    if _has_insurance_module:
        rate = invoice.get_rate("insurance")
        if not rate:
            rate = 0
    else:
        if invoice.insurance:
            rate = invoice.insurance.rate
        else:
            rate = 0
    datas.append("{} %".format(rate))

    if _has_insurance_module:
        insurance = invoice.total_insurance(invoice.ht)
        rounded = translate_integer_precision(insurance)
    else:
        if invoice.insurance:
            insurance = invoice.total_insurance(invoice.ht)
            rounded = translate_integer_precision(insurance)
        else:
            rounded = 0
    datas.append(integer_to_amount(rounded, precision=2))
    datas.append(invoice.start_date)
    datas.append(invoice.end_date)
    writer.add_extra_datas(datas)
    return writer


def _add_estimation_datas(writer, invoice):
    _has_insurance_module = False
    if CustomInvoiceBookEntryModule.get_by_name("insurance", invoice.prefix):
        _has_insurance_module = True

    ht_values = invoice.tva_ht_parts()
    tva_values = invoice.get_tvas()
    datas = []
    datas.append(integer_to_amount(invoice.ht, precision=5))
    datas.append(integer_to_amount(invoice.ttc, precision=5))
    for tva in Tva.query():
        datas.append(integer_to_amount(ht_values.get(tva, 0), precision=5))
        datas.append(integer_to_amount(tva_values.get(tva, 0), precision=5))

    if invoice.insurance:
        datas.append(invoice.insurance.label)
    else:
        if not _has_insurance_module:
            datas.append("")
        else:
            level = invoice.get_rate_level("insurance")
            if level == "cae":
                datas.append("Taux de la CAE (module assurance)")
            elif level == "company":
                datas.append("Taux d'assurance de l'enseigne")
            else:
                datas.append("")

    if _has_insurance_module:
        rate = invoice.get_rate("insurance")
        if not rate:
            rate = 0
    else:
        if invoice.insurance:
            rate = invoice.insurance.rate
        else:
            rate = 0
    datas.append("{} %".format(rate))

    if _has_insurance_module:
        insurance = invoice.total_insurance(invoice.ht)
        rounded = translate_integer_precision(insurance)
    else:
        if invoice.insurance:
            insurance = invoice.total_insurance(invoice.ht)
            rounded = translate_integer_precision(insurance)
        else:
            rounded = 0
    datas.append(integer_to_amount(rounded, precision=2))
    writer.add_extra_datas(datas)
    return writer


def _add_supplier_invoice_custom_headers(writer, supplier_invoices):
    writer.add_extra_header({"label": "Montant HT", "name": "ht"})
    writer.add_extra_header({"label": "Montant TVA", "name": "tva"})
    writer.add_extra_header({"label": "Montant TTC", "name": "ttc"})
    writer.add_extra_header({"label": "Type", "name": "typ"})
    writer.add_extra_header({"label": "Statut", "name": "status"})
    return writer


def _add_supplier_invoice_data(writer, supplier_invoice):
    """Add Supplier invoice related information to the export"""
    typ = "Externe"
    if isinstance(supplier_invoice, InternalSupplierInvoice):
        typ = "Interne"

    status = format_supplier_invoice_status(supplier_invoice, full=False)

    writer.add_extra_datas(
        [
            integer_to_amount(supplier_invoice.total_ht, precision=2),
            integer_to_amount(supplier_invoice.total_tva, precision=2),
            integer_to_amount(supplier_invoice.total, precision=2),
            typ,
            status,
        ]
    )
    return writer


def _import_userdatas_add_related_user(action, dbsession, model, updated, args):
    """
    Creat a User instance when importing a new UserDatas instance

    :param str action: An import action (override, insert, update, only_update,
    only_override)
    :param obj dbsession: The database transaction session (DBSESSION)
    :param obj model: The newly inserted model
    :param bool updated: Is it an update of an existing model ?
    :param dict args: The importation arguments
    """
    if action == "insert":
        model.gen_related_user_instance()
    return model


def _import_third_party_set_label(action, dbsession, model, updated, args):
    """
    Ensure the currently managed model has a label set
    """
    if not model.label:
        model.label = model._get_label()
        model = dbsession.merge(model)
    if not model.name:
        model.name = model.label
        model = dbsession.merge(model)
    return model


def _import_third_party_set_type_(type_, action, dbsession, model, updated, args):
    """
    Set the polymorphic key type_ on the model
    """
    if not model.type_:
        model.type_ = type_
        model = dbsession.merge(model)
    return model


def includeme(config):
    configure_export()
    config.register_import_model(
        key="userdatas",
        model=UserDatas,
        label="Données de gestion sociale",
        permission=PERMISSIONS["global.view_userdata_details"],
        excludes=(
            "name",
            "created_at",
            "updated_at",
            "type_",
            "_acl",
            "parent_id",
            "parent",
        ),
        callbacks=[_import_userdatas_add_related_user],
    )
    config.register_import_model(
        key="customers",
        model=Customer,
        label="Clients",
        permission=PERMISSIONS["context.add_customer"],
        excludes=(
            "created_at",
            "updated_at",
            "company_id",
            "company",
            "type_",
        ),
        callbacks=[
            _import_third_party_set_label,
            functools.partial(_import_third_party_set_type_, "customer"),
        ],
    )
    config.register_import_model(
        key="suppliers",
        model=Supplier,
        label="Fournisseurs",
        permission=PERMISSIONS["context.add_supplier"],
        excludes=(
            "created_at",
            "updated_at",
            "company_id",
            "company",
            "type_",
        ),
        callbacks=[
            _import_third_party_set_label,
            functools.partial(_import_third_party_set_type_, "customer"),
        ],
    )
    config.register_export_model(
        key="userdatas",
        model=UserDatas,
        options={
            "hook_init": _add_userdatas_custom_headers,
            "hook_add_row": _add_userdatas_code_compta,
            "foreign_key_name": "userdatas_id",
            "excludes": (
                "name",
                "type_",
                "_acl",
                "parent_id",
                "parent",
            ),
        },
    )
    config.register_export_model(
        key="invoices",
        model=Task,
        options={
            "hook_init": _add_invoice_custom_headers,
            "hook_add_row": _add_invoice_datas,
            "foreign_key_name": "task_id",
            "excludes": ("name", "created_at", "updated_at", "type_"),
            "order": (
                "company",
                "customer",
                "date",
                "official_number",
                "description",
                "workplace",
            ),
        },
    )
    config.register_export_model(
        key="supplier_invoices",
        model=SupplierInvoice,
        options={
            "hook_init": _add_supplier_invoice_custom_headers,
            "hook_add_row": _add_supplier_invoice_data,
            "foreign_key_name": "supplier_invoice_id",
            "excludes": (
                "name",
                "created_at",
                "updated_at",
                "type_",
                "supplier_orders",
                "lines",
                "exports",
                "exported",
            ),
            "order": (
                "company",
                "supplier",
                "date",
                "official_number",
                "remote_invoice_number",
                "exported",
                "cae_percentage",
                "payer",
            ),
        },
    )
    config.register_export_model(
        key="accounting_operations",
        model=AccountingOperation,
        options={
            "foreign_key_name": "id",
            "order": (
                "date",
                "general_account",
                "label",
                "debit",
                "credit",
                "balance",
                "analytical_account",
                "company",
            ),
        },
    )
    config.register_export_model(
        key="estimations",
        model=Task,
        options={
            "hook_init": _add_estimation_custom_headers,
            "hook_add_row": _add_estimation_datas,
            "foreign_key_name": "task_id",
            "excludes": ("name", "created_at", "updated_at", "type_"),
            "order": (
                "company",
                "customer",
                "date",
                "description",
                "workplace",
            ),
        },
    )

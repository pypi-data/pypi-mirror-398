"""
Third party handling forms schemas and related widgets
"""
from collections import OrderedDict

import colander
import deform
import pyvat
from colanderalchemy import SQLAlchemySchemaNode
from pyramid_deform import CSRFSchema
from sqlalchemy import asc, not_, select
from stdnum.fr import siren, siret

from caerp import forms
from caerp.consts.civilite import CIVILITE_OPTIONS, EXTENDED_CIVILITE_OPTIONS
from caerp.consts.permissions import PERMISSIONS
from caerp.forms.company import company_choice_node
from caerp.models.company import Company
from caerp.models.third_party import ThirdParty
from caerp.models.third_party.supplier import Supplier


def _build_third_party_select_value(third_party):
    """
    Return the tuple for building third_party select
    """
    return (third_party.id, third_party.label)


def build_third_party_values(third_parties):
    """
    Build human understandable third_party labels
    allowing efficient discrimination

    :param obj third_parties: Iterable (list or Sqlalchemy query)
    :returns: A list of 2-uples
    """
    return [
        _build_third_party_select_value(third_party) for third_party in third_parties
    ]


def build_admin_third_party_options(query):
    """
    Format options for admin third_party select widget

    :param obj query: The Sqlalchemy query
    :returns: A list of deform.widget.OptGroup
    """
    query = query.order_by(Company.name)
    values = []
    datas = OrderedDict()

    for item in query:
        datas.setdefault(item.company.name, []).append(
            _build_third_party_select_value(item)
        )

    # All third_parties, grouped by Company
    for company_name, third_parties in list(datas.items()):
        values.append(deform.widget.OptGroup(company_name, *third_parties))
    return values


@colander.deferred
def deferred_default_type(node, kw):
    """
    Set the default third_party type based on the current (if in edition mode)
    """
    if isinstance(kw["request"].context, ThirdParty):
        return kw["request"].context.type
    else:
        return colander.null


def siret_validator(node, value):
    """
    Validator for SIRET

    Raise a colander.Invalid exception when the value is not a valid SIRET
    """
    value = value.strip().replace(" ", "")
    if not siret.is_valid(value) and not siren.is_valid(value):
        raise colander.Invalid(node, "SIRET invalide")


def tva_intracomm_validator(node, value):
    """
    Validator for VAT number

    Raise a colander.Invalid exception when the value is not a valid vat number
    """
    if not pyvat.is_vat_number_format_valid(value):
        raise colander.Invalid(node, "Numéro de TVA intracommunautaire invalide")


def company_identification_number_validator(form, appstruct):
    """
    Validator for company's identification number

    Raise a colander.Invalid exception when neither 'siret' or 'registration' fields
    are filled
    """
    if not appstruct.get("siret") and not appstruct.get("registration"):
        raise colander.Invalid(
            form, "Le SIRET ou le numéro d'immatriculation est obligatoire"
        )


def customize_third_party_schema(schema):
    """
    Add common widgets configuration for the third parties forms schema

    :param obj schema: The ThirdParty form schema
    """
    if "type" in schema:
        schema["type"].validator = colander.OneOf(["individual", "company", "internal"])
        schema["type"].default = deferred_default_type

    if "civilite" in schema:
        schema["civilite"].widget = forms.get_select(CIVILITE_OPTIONS)
        schema["civilite"].validator = colander.OneOf([a[0] for a in CIVILITE_OPTIONS])

    if "additional_address" in schema:
        schema["additional_address"].widget = deform.widget.TextAreaWidget(
            cols=25,
            row=1,
        )

    if "city_code" in schema:
        schema["city_code"].widget = deform.widget.HiddenWidget()

    if "country_code" in schema:
        schema["country_code"].widget = deform.widget.HiddenWidget()

    if "email" in schema:
        schema["email"].validator = forms.mail_validator()

    if "compte_cg" in schema:
        msg = "Laisser vide pour utiliser les paramètres de l'enseigne"
        schema["compte_cg"].description = msg
        schema["compte_tiers"].description = msg

    if "siret" in schema:
        schema["siret"].validator = siret_validator

    if "tva_intracomm" in schema:
        schema["tva_intracomm"].validator = tva_intracomm_validator

    schema.children.append(CSRFSchema()["csrf_token"])

    if "type" in schema:
        schema["type"].validator = colander.OneOf(["individual", "company", "internal"])
        schema["type"].default = deferred_default_type

    if "bank_account_bic" in schema:
        schema["bank_account_bic"].validator = colander.All(
            forms.bic_validator,
            colander.Length(max=11),
        )
        schema["bank_account_bic"].preparer = forms.remove_spaces_string_preparer
    if "bank_account_iban" in schema:
        schema["bank_account_iban"].validator = colander.All(
            forms.iban_validator,
            colander.Length(max=34),
        )
        schema["bank_account_iban"].preparer = forms.remove_spaces_string_preparer

    return schema


def customize_individual_schema(schema):
    """
    Add specific widgets configuration for the individual forms schema

    :param obj schema: The individual third party form schema
    """
    # Override default civilite
    schema["civilite"].widget = forms.get_select(
        EXTENDED_CIVILITE_OPTIONS,
    )
    schema["civilite"].validator = colander.OneOf(
        [a[0] for a in EXTENDED_CIVILITE_OPTIONS]
    )
    return schema


def third_party_after_bind(schema, kw):
    """
    After bind method for the third_party model schema

    Removes nodes if the user have no rights to edit them

    :param obj schema: Schema corresponding to the ThirdParty
    :param dict kw: The bind parameters
    """
    request = kw["request"]
    if not request.has_permission(
        PERMISSIONS["global.manage_accounting"], request.context
    ):
        for key in (
            "compte_cg",
            "compte_tiers",
            "bank_account_bic",
            "bank_account_iban",
            "bank_account_owner",
        ):
            if key in schema:
                del schema[key]


def get_individual_third_party_schema(third_party_class=ThirdParty, more_excludes=None):
    """
    Build an individual third party form schema

    :return: The schema
    """
    excludes = [
        "name",
        "company_name",
        "tva_intracomm",
        "function",
        "registration",
        "siret",
    ]
    if more_excludes is not None:
        excludes.extend(more_excludes)

    schema = SQLAlchemySchemaNode(third_party_class, excludes=excludes)
    schema = customize_third_party_schema(schema)
    schema = customize_individual_schema(schema)
    schema["firstname"].title = "Prénom"
    schema["lastname"].title = "Nom"
    schema["lastname"].missing = colander.required
    schema.after_bind = third_party_after_bind
    if "siret" in schema and third_party_class != Supplier:
        schema.validator = company_identification_number_validator
    return schema


def get_company_third_party_schema(third_party_class=ThirdParty, more_excludes=None):
    """
    return the schema for user add/edit regarding the current user's role
    """
    excludes = ["name"]
    if more_excludes is not None:
        excludes.extend(more_excludes)

    schema = SQLAlchemySchemaNode(third_party_class, excludes=excludes)
    schema = customize_third_party_schema(schema)
    schema["company_name"].missing = colander.required
    schema["api_last_update"].widget = deform.widget.HiddenWidget()
    schema.after_bind = third_party_after_bind
    return schema


def get_internal_third_party_schema(third_party_class=ThirdParty, edit=False):
    if not edit:
        return get_internal_third_party_add_schema(third_party_class)
    else:
        return get_internal_third_party_edit_schema(third_party_class)


def get_internal_third_party_add_schema(third_party_class=ThirdParty):
    """
    Build a schema to add an internal third party
    """
    schema = colander.Schema()
    schema.add(
        colander.SchemaNode(
            name="type",
            typ=colander.String(),
            default="internal",
            missing=colander.required,
        )
    )
    schema.add(
        company_choice_node(
            name="source_company_id",
            title="Enseigne",
            widget_options={"query": company_query_for_internal_third_party},
            validator=company_employees_validator,
        )
    )
    schema.add(
        colander.SchemaNode(
            name="company_id",
            typ=colander.Integer(),
            widget=deform.widget.HiddenWidget(),
            default=default_current_context_id,
            missing=default_current_context_id,
        )
    )

    def create_third_party_from_company_id(appstruct, model=None):
        if model is None:
            company_id = appstruct.pop("source_company_id")
            owner_company_id = appstruct.pop("company_id")
            if company_id == owner_company_id:
                raise colander.Invalid("Erreur : on ne peut se facturer à soi-même")
            company = Company.get(company_id)
            owner_company = Company.get(owner_company_id)
            model = third_party_class.from_company(company, owner_company)
        else:
            appstruct.pop("company_id", None)
        forms.merge_session_with_post(model, appstruct)
        return model

    schema["source_company_id"].missing = colander.required
    schema.objectify = create_third_party_from_company_id
    return schema


def get_internal_third_party_edit_schema(third_party_class=ThirdParty):
    excludes = (
        "name",
        "tva_intracomm",
        "registration",
        "siret",
    )
    schema = SQLAlchemySchemaNode(third_party_class, excludes=excludes)
    schema = customize_third_party_schema(schema)
    schema["company_name"].missing = colander.required
    schema.after_bind = third_party_after_bind
    return schema


def company_query_for_internal_third_party(request):
    """
    Build a query to collect the company ids that we propose in the internal
    third party form

    excludes already used company ids and current's company id

    :returns: a Sqlalchemy Query
    """
    company = request.context

    # Collecte des enseignes dont on ne veut pas dans le formulaire
    company_ids = [company.id]
    company_id_query = select(ThirdParty.source_company_id).where(
        ThirdParty.company_id == company.id,
        ThirdParty.source_company_id != None,  # noqa: E711
    )
    company_ids.extend(request.dbsession.execute(company_id_query).scalars().all())

    query = (
        select(Company.id, Company.name)
        .where(Company.active == True, not_(Company.id.in_(company_ids)))
        .order_by(asc(Company.name))
    )
    return request.dbsession.execute(query)


@colander.deferred
def default_current_context_id(node, kw):
    """
    Return the default current context id as company_id
    """
    return kw["request"].context.id


def company_employees_validator(node, company_id):
    company = Company.get(company_id)
    if not company:
        raise colander.Invalid(node, "Enseigne introuvable")
    if len(company.get_active_employees()) == 0:
        raise colander.Invalid(node, "Cette enseigne n'est associée à aucun compte")

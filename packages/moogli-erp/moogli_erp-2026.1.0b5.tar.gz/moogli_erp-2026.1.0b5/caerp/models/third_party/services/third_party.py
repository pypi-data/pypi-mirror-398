from sqlalchemy import func
from sqlalchemy.orm import load_only

from caerp.models.base import DBSESSION
from caerp.models.company import Company
from caerp.models.config import Config


class ThirdPartyService:
    @classmethod
    def get_label(cls, instance, with_company_contact=False):
        label = ""
        if instance.type in ("company", "internal"):
            if instance.internal_name:
                label = instance.internal_name
            else:
                label = instance.company_name
            if with_company_contact:
                label += f"\n{instance.get_contact_label()}"
        else:
            label = instance.get_contact_label()
        return label

    @classmethod
    def get_full_address(cls, instance, with_company_contact=True):
        """
        Return the third_party full coordinates (name + address)
        formatted in french format
        """
        return "{0}\n{1}".format(
            cls.get_label(instance, with_company_contact=with_company_contact),
            instance.get_postal_address(),
        )

    @classmethod
    def label_query(cls, third_party_class):
        """
        Return a query loading datas needed to compile ThirdParty label
        """
        query = third_party_class.query()
        query = query.options(
            load_only(
                "id",
                "label",
                "company_id",
            )
        )
        return query

    @staticmethod
    def get_by_label(cls, label: str, company: Company, case_sensitive: bool = False):
        """
        Even if case_sensitive == True, exact match is preferred.
        """
        query = cls.query().filter(
            cls.archived == False,  # noqa: E712
            cls.company == company,
        )
        exact_match = query.filter(cls.label == label).one_or_none()

        if exact_match or case_sensitive:
            return exact_match
        else:
            insensitive_match = query.filter(
                func.lower(cls.label) == func.lower(label)
            ).one_or_none()
            return insensitive_match

    @staticmethod
    def create_third_party_from_internal_company(
        cls, source_company: Company, owner_company: Company
    ) -> "ThirdParty":
        """
        Build up a Third party instance from an internal company

        :param obj source_company: Company we want to create a ThirdParty from
        :param obj owner_company: Which company the ThirdParty belongs to

        :returns: A new ThirdParty instance
        """
        query = cls.query().filter_by(
            source_company_id=source_company.id, company_id=owner_company.id
        )
        edit = False
        if query.count() > 0:
            model = query.first()
            model.archived = False
            edit = True
        else:
            model = cls(type="internal")
            model.company_name = source_company.name
        model.source_company_id = source_company.id

        # Si on a bien un seul employé actif on l'utilise comme contact
        active_employees = source_company.get_active_employees()
        if len(active_employees) == 0:
            raise Exception("No active employee")
        if len(active_employees) == 1:
            model.lastname = active_employees[0].lastname
            model.firstname = active_employees[0].firstname
            model.civilite = active_employees[0].civilite

        model.email = source_company.email
        model.address = Config.get_value("cae_address")
        model.zip_code = Config.get_value("cae_zipcode")
        model.city = Config.get_value("cae_city")
        model.company_id = owner_company.id
        model.label = model._get_label()
        if edit:
            DBSESSION().merge(model)
            DBSESSION().flush()
        else:
            DBSESSION().add(model)
            DBSESSION().flush()
        return model

    @classmethod
    def get_third_party_account(cls, instance):
        raise NotImplementedError("get_third_party_account")

    @classmethod
    def get_general_account(cls, instance):
        raise NotImplementedError("get_general_account")

    @classmethod
    def get_company_identification_number(cls, instance):
        if instance.siret:
            return instance.siret
        else:
            return instance.registration

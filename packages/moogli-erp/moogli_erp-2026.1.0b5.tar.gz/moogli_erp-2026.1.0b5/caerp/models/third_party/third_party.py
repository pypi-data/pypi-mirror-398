"""
    ThirdParty model
"""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.event import listen, remove
from sqlalchemy.orm import relationship

from caerp.models.base import default_table_args
from caerp.models.company import Company
from caerp.models.listeners import SQLAListeners
from caerp.models.node import Node
from caerp.models.third_party.mixins import ContactMixin, PostalAddressMixin
from caerp.utils.compat import Iterable

from ..status import StatusLogEntry, status_history_relationship
from .services.third_party import ThirdPartyService


class ThirdParty(Node, PostalAddressMixin, ContactMixin):
    __tablename__ = "third_party"
    __table_args__ = default_table_args
    __mapper_args__ = {"polymorphic_identity": "third_party"}
    _caerp_service = ThirdPartyService

    id = Column(
        Integer,
        ForeignKey("node.id"),
        primary_key=True,
        info={"colanderalchemy": {"exclude": True}},
    )
    company_id = Column(
        "company_id",
        Integer,
        ForeignKey("company.id"),
        info={"export": {"exclude": True}},
        nullable=False,
    )
    # Type de tiers : company/individual/internal
    type = Column(
        "type",
        String(10),
        default="company",
        info={
            "colanderalchemy": {"title": "Type"},
            "export": {"label": "Type"},
        },
    )
    # Label utilisé dans l'interface, mis à jour en fonction du type
    label = Column(
        "label",
        String(255),
        info={"colanderalchemy": {"exclude": True}},
        default="",
    )
    # Champs spécifiques aux personnes morales
    company_name = Column(
        "company_name",
        String(255),
        info={"colanderalchemy": {"title": "Raison sociale"}},
        default="",
    )
    internal_name = Column(
        "internal_name",
        String(255),
        info={"colanderalchemy": {"title": "Nom interne"}},
        default="",
    )
    siret = Column(
        "siret",
        String(14),
        info={"colanderalchemy": {"title": "Numéro SIRET (ou SIREN)"}},
        default="",
        index=True,
    )
    registration = Column(
        "registration",
        String(255),
        info={"colanderalchemy": {"title": "Numéro d'immatriculation"}},
        default="",
    )
    tva_intracomm = Column(
        "tva_intracomm",
        String(50),
        info={"colanderalchemy": {"title": "TVA intracommunautaire"}},
        default="",
    )
    # Champs comptables
    compte_cg = Column(
        String(125),
        info={"colanderalchemy": {"title": "Compte CG"}},
        default="",
    )
    compte_tiers = Column(
        String(125),
        info={"colanderalchemy": {"title": "Compte tiers"}},
        default="",
    )
    # Champs à usage interne
    archived = Column(
        Boolean(),
        default=False,
        info={"colanderalchemy": {"exclude": True}},
    )
    api_last_update = Column(
        DateTime(),
        nullable=True,
        info={"export": {"exclude": True}},
    )
    source_company_id = Column(
        "source_company_id",
        Integer,
        ForeignKey("company.id", ondelete="SET NULL"),
        info={
            "export": {"exclude": True},
            "colanderalchemy": {"exclude": True},
        },
        nullable=True,
    )
    bank_account_bic = Column(
        String(12),
        info={
            "colanderalchemy": {
                "title": "BIC",
                "description": "BIC du compte bancaire",
            }
        },
    )
    bank_account_iban = Column(
        String(35),
        info={
            "colanderalchemy": {
                "title": "IBAN",
                "description": "IBAN du compte bancaire, sans espace entre les chiffres",
            }
        },
    )
    bank_account_owner = Column(
        String(100),
        info={
            "colanderalchemy": {
                "title": "Titulaire",
                "description": "Civilité, Nom et Prénom du titulaire du compte",
            }
        },
    )
    source_company = relationship(
        "Company",
        primaryjoin="Company.id==ThirdParty.source_company_id",
        info={
            "colanderalchemy": {"exclude": True},
            "export": {"exclude": True},
        },
    )
    statuses = status_history_relationship()

    def extra_statuses(self) -> Iterable[StatusLogEntry]:
        # Node children contribute to my history
        # Used for eg in sap_urssaf3p plugin to provide registration status
        for child in self.children:
            yield from child.statuses

    def __json__(self, request):
        """
        :returns: a dict version of the third_party object
        """
        return dict(
            id=self.id,
            created_at=self.created_at.isoformat(),
            updated_at=self.updated_at.isoformat(),
            company_id=self.company_id,
            type=self.type,
            label=self.label,
            company_name=self.company_name,
            internal_name=self.internal_name,
            civilite=self.civilite,
            lastname=self.lastname,
            firstname=self.firstname,
            function=self.function,
            siret=self.siret,
            registration=self.registration,
            tva_intracomm=self.tva_intracomm,
            address=self.address,
            additional_address=self.additional_address,
            zip_code=self.zip_code,
            city=self.city,
            city_code=self.city_code,
            country=self.country,
            country_code=self.country_code,
            full_address=self.full_address,
            email=self.email,
            mobile=self.mobile,
            phone=self.phone,
            compte_cg=self.compte_cg,
            compte_tiers=self.compte_tiers,
            archived=self.archived,
            api_last_update=self.api_last_update,
            status_history=[
                status.__json__(request)
                for status in self.get_allowed_statuses(request)
            ],
            bank_account_bic=self.bank_account_bic,
            bank_account_iban=self.bank_account_iban,
            bank_account_owner=self.bank_account_owner,
        )

    def get_company_id(self):
        return self.company.id

    @property
    def full_address(self):
        return self._caerp_service.get_full_address(self)

    def is_deletable(self):
        return self.archived

    def is_company(self):
        return self.type == "company"

    def is_internal(self):
        return self.type == "internal"

    def _get_label(self):
        return self._caerp_service.get_label(self)

    @classmethod
    def label_query(cls):
        return cls._caerp_service.label_query(cls)

    def get_general_account(self, prefix=""):
        return self._caerp_service.get_general_account(self, prefix)

    def get_third_party_account(self, prefix=""):
        return self._caerp_service.get_third_party_account(self, prefix)

    @classmethod
    def get_by_label(cls, label: str, company: "Company", case_sensitive: bool = False):
        return cls._caerp_service.get_by_label(cls, label, company, case_sensitive)

    @classmethod
    def from_company(
        cls, source_company: Company, owner_company: Company
    ) -> "ThirdParty":
        return cls._caerp_service.create_third_party_from_internal_company(
            cls, source_company, owner_company
        )

    def get_company_identification_number(self):
        return self._caerp_service.get_company_identification_number(self)


def set_third_party_label(mapper, connection, target):
    target.label = target._get_label()
    target.name = target.label


def start_listening():
    listen(ThirdParty, "before_insert", set_third_party_label, propagate=True)
    listen(ThirdParty, "before_update", set_third_party_label, propagate=True)


def stop_listening():
    remove(ThirdParty, "before_insert", set_third_party_label)
    remove(ThirdParty, "before_update", set_third_party_label)


SQLAListeners.register(start_listening, stop_listening)

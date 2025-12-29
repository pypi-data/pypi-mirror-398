"""
    Model for tva amounts
"""
import deform.widget
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, not_
from sqlalchemy.orm import relationship

from caerp.compute.math_utils import integer_to_amount
from caerp.models.base import DBBASE, DBSESSION, default_table_args


class Tva(DBBASE):
    __tablename__ = "tva"
    __table_args__ = default_table_args
    id = Column("id", Integer, primary_key=True)
    active = Column(Boolean(), default=True)
    name = Column("name", String(15), nullable=False)
    value = Column("value", Integer, nullable=False)
    compte_cg = Column("compte_cg", String(125), default="")
    code = Column("code", String(125), default="")
    compte_a_payer = Column(String(125), default="")
    mention = Column(Text)
    default = Column("default", Boolean())
    compte_client = Column("compte_client", String(125), default="")

    products = relationship(
        "Product",
        cascade="all, delete-orphan",
        back_populates="tva",
        order_by="Product.order",
    )

    @classmethod
    def query(cls, include_inactive=False):
        q = super(Tva, cls).query()
        if not include_inactive:
            q = q.filter(Tva.active == True)  # NOQA: E712
        return q.order_by("value")

    @classmethod
    def by_value(cls, value, or_none=False):
        """
        Returns the Tva matching this value
        """
        query = super(Tva, cls).query().filter(cls.value == value)
        if or_none:
            return query.one_or_none()
        else:
            return query.one()

    def __repr__(self) -> str:
        return (
            f"<Tva id={self.id} name={self.name} value={self.value}"
            f"compte_cg={self.compte_cg} active={self.active}>"
        )

    def __json__(self, request):
        return dict(
            id=self.id,
            value=integer_to_amount(self.value, 2),
            label=self.name,
            name=self.name,
            default=self.default,
            products=[product.__json__(request) for product in self.products],
        )

    @classmethod
    def unique_value(cls, value, tva_id=None):
        """
        Check that the given value has not already been attributed to a tva
        entry

        :param int value: The value currently configured
        :param int tva_id: The optionnal id of the current tva object (edition
        mode)
        :returns: True/False
        :rtype: bool
        """
        query = cls.query(include_inactive=True)
        if tva_id:
            query = query.filter(not_(cls.id == tva_id))

        return query.filter_by(value=value).count() == 0

    @property
    def rate(self):
        """
        Return the display value

        20 for 20% tva rate
        """
        value = max(self.value, 0)
        return integer_to_amount(value, 2)

    @property
    def ratio(self):
        """
        Return the ratio applied

        0.2 for 20% tva rate
        """
        value = max(self.value, 0)
        return integer_to_amount(value, 4)


class Product(DBBASE):
    __tablename__ = "product"
    __table_args__ = default_table_args
    id = Column("id", Integer, primary_key=True)
    name = Column("name", String(125), nullable=False)
    order = Column(
        "order",
        Integer,
        nullable=False,
        default=0,
        info={"colanderalchemy": {"exclude": True}},
    )
    compte_cg = Column("compte_cg", String(125))
    active = Column(Boolean(), default=True)
    internal = Column(Boolean(), default=False)
    tva_id = Column(
        Integer,
        ForeignKey("tva.id", ondelete="cascade"),
        info={"colanderalchemy": {"exclude": True}},
    )
    tva = relationship(
        "Tva", back_populates="products", info={"colanderalchemy": {"exclude": True}}
    )
    # Belongs to urssaf_3p but by commodity we store it here
    urssaf_code_nature = Column(
        String(10),
        nullable=False,
        default="",
        info={"colanderalchemy": {"widget": deform.widget.HiddenWidget()}},
    )

    def __repr__(self) -> str:
        return (
            f"<Product(id={self.id}, name='{self.name}', compte_cg={self.compte_cg}"
            f" active={self.active} tva_id={self.tva_id})>"
        )

    def __json__(self, request):
        return dict(
            id=self.id,
            name=self.name,
            label=self.name,
            compte_cg=self.compte_cg,
            tva_id=self.tva_id,
        )

    @classmethod
    def query(cls, include_inactive=False):
        q = super(Product, cls).query()
        if not include_inactive:
            q = q.join(cls.tva)
            q = q.filter(Product.active == True)  # NOQA E712
            q = q.filter(Tva.active == True)  # NOQA E712
        return q.order_by("order")

    @classmethod
    def firts_by_tva_id(cls, tva_id, internal=False):
        """
        Return a Product instance
        """
        return (
            DBSESSION()
            .query(Product)
            .filter(
                cls.active.is_(True),
                cls.internal.is_(internal),
                cls.tva_id == tva_id,
            )
            .first()
        )

from colanderalchemy import SQLAlchemySchemaNode
from sqlalchemy import func, desc

from caerp.forms.third_party.customer import (
    get_company_customer_schema,
    get_individual_customer_schema,
    get_internal_customer_schema,
)
from caerp.models.third_party.customer import Customer
from caerp.models.project.project import ProjectCustomer
from caerp.utils.controller import RelatedAttrManager

from ..controller import ThirdPartyAddEditController


class CustomerRelatedAttrManager(RelatedAttrManager):
    def _add_related_project_ids(self, customer, customer_dict):
        result = self.dbsession.query(ProjectCustomer.c.project_id).filter(
            ProjectCustomer.c.customer_id == customer.id
        )
        customer_dict["project_ids"] = [p[0] for p in result]
        return customer_dict


class CustomerAddEditController(ThirdPartyAddEditController):
    related_manager_factory = CustomerRelatedAttrManager

    def get_company_schema(self) -> SQLAlchemySchemaNode:
        return get_company_customer_schema()

    def get_individual_schema(self) -> SQLAlchemySchemaNode:
        return get_individual_customer_schema()

    def get_internal_schema(self) -> SQLAlchemySchemaNode:
        return get_internal_customer_schema(edit=self.edit)

    def get_default_type(self) -> str:
        result = "company"
        if not isinstance(self.context, Customer):
            # On cherche le type de client que cette enseigne utilise
            query_result = (
                self.request.dbsession.query(
                    Customer.type, func.count(Customer.id).label("count")
                )
                .filter(
                    Customer.type.in_(["individual", "company"]),
                    Customer.company_id == self.context.id,
                )
                .group_by("type")
                .order_by(desc("count"))
                .first()
            )

            if query_result is not None:
                result = query_result[0]
        return result

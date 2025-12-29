import colander
from sqlalchemy import or_

from caerp.models.company import Company
from caerp.models.user import User
from caerp.models.workshop import Workshop


class CaeWorkshopFilterMixin:
    """
    Filter set for workshops beloging to the CAE (= no company or internal company)
    """

    def filter_company_manager_or_cae(self, query, appstruct):
        company_manager = appstruct.get("company_manager")
        if company_manager == colander.null:
            query = query.filter(Workshop.company_manager_id == None)  # noqa: E711
        elif company_manager is not None:
            if company_manager in (-1, "-1"):
                query = query.outerjoin(Workshop.company_manager).filter(
                    or_(
                        Workshop.company_manager_id == None,  # noqa: E711
                        Company.internal == True,
                    )
                )
            else:
                query = query.filter(
                    Workshop.company_manager_id == int(company_manager)
                )
        return query


class CompanyWorkshopFilterMixin:
    """
    Filter set for workshops belonging to a specific company
    """

    def filter_company_manager_or_cae(self, query, appstruct):
        # Totaly ignore appstruct filters
        company = self.context
        employee_ids = company.get_employee_ids()
        query = query.filter(
            or_(
                Workshop.company_manager_id == company.id,
                Workshop.trainers.any(User.id.in_(employee_ids)),
            )
        )
        return query

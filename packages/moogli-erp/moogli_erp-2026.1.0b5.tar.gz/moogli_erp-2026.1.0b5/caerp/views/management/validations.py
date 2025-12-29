import datetime
import logging

import colander
from dateutil.relativedelta import relativedelta
from sqlalchemy import or_
from sqlalchemy.orm import with_polymorphic

from caerp.consts.permissions import PERMISSIONS
from caerp.export.excel import XlsExporter
from caerp.export.ods import OdsExporter
from caerp.export.utils import write_file_to_request
from caerp.forms.management.validations import get_list_schema
from caerp.models.expense import ExpenseSheet
from caerp.models.node import Node
from caerp.models.status import StatusLogEntry
from caerp.models.supply import SupplierInvoice, SupplierOrder
from caerp.models.task import Task
from caerp.services.node import get_node_label
from caerp.views import BaseListView

logger = logging.getLogger(__name__)


class ValidationsManagementView(BaseListView):
    """
    Tableau de suivi des validations
    """

    schema = get_list_schema()
    use_paginate = False
    default_sort = "date"
    sort_columns = {"date": "datetime"}

    node_polymorphic = with_polymorphic(
        Node, [ExpenseSheet, Task, SupplierOrder, SupplierInvoice]
    )

    title = "Suivi des validations"

    def query(self):
        return (
            StatusLogEntry.query()
            .join(self.node_polymorphic)
            .where(
                or_(
                    StatusLogEntry.state_manager_key == "status",
                    StatusLogEntry.state_manager_key == "validation_status",
                )
            )
            .order_by(StatusLogEntry.datetime)
        )

    def filter_user(self, query, appstruct):
        user_id = appstruct.get("user_id")
        if user_id not in (None, colander.null, "all"):
            query = query.filter(StatusLogEntry.user_id == user_id)
        return query

    def filter_company(self, query, appstruct):
        company_id = appstruct.get("company_id")
        if company_id not in (None, colander.null, "all"):
            query = query.filter(
                or_(
                    self.node_polymorphic.ExpenseSheet.company_id == company_id,
                    self.node_polymorphic.Task.company_id == company_id,
                    self.node_polymorphic.SupplierOrder.company_id == company_id,
                    self.node_polymorphic.SupplierInvoice.company_id == company_id,
                )
            )
        return query

    def filter_type(self, query, appstruct):
        type = appstruct.get("type")
        if type not in (None, colander.null, "all"):
            query = query.filter(
                or_(Node.type_ == type, Node.type_ == "internal" + type)
            )
        return query

    def filter_result(self, query, appstruct):
        result = appstruct.get("result")
        if result not in (None, colander.null, "all"):
            query = query.filter(StatusLogEntry.status == result)
        else:
            query = query.filter(
                or_(
                    StatusLogEntry.status == "valid",
                    StatusLogEntry.status == "invalid",
                )
            )
        return query

    def filter_period(self, query, appstruct):
        year = appstruct.get("year")
        if year not in (None, colander.null):
            self.year = year
        else:
            self.year = datetime.date.today().year
        month = appstruct.get("month")
        if month not in (None, colander.null):
            self.month = month
        else:
            self.month = datetime.date.today().month
        period_start = datetime.date(int(year), int(month), 1)
        period_end = period_start + relativedelta(months=1)
        period_end = period_end - relativedelta(days=1)
        query = query.filter(StatusLogEntry.datetime.between(period_start, period_end))
        return query

    def filter_year(self, query, appstruct):
        return self.filter_period(query, appstruct)

    def filter_month(self, query, appstruct):
        return self.filter_period(query, appstruct)

    def more_template_vars(self, response_dict):
        response_dict["export_xls_url"] = self.request.route_path(
            "management_validations_export",
            extension="xls",
            _query=self.request.GET,
        )
        response_dict["export_ods_url"] = self.request.route_path(
            "management_validations_export",
            extension="ods",
            _query=self.request.GET,
        )
        return response_dict


class ValidationsManagementXlsView(ValidationsManagementView):
    """
    Export du tableau de suivi des validations au format XLSX
    """

    _factory = XlsExporter

    @property
    def filename(self):
        return "suivi_validations_{}_{}.{}".format(
            self.year,
            self.month,
            self.request.matchdict["extension"],
        )

    def _init_writer(self):
        writer = self._factory()
        headers = [
            "Date",
            "Validateur",
            "Enseigne",
            "Type",
            "Nom",
            "Résultat",
        ]
        writer.add_headers(headers)
        return writer

    def _build_return_value(self, schema, appstruct, query):
        writer = self._init_writer()
        writer._datas = []
        for data in query.all():
            row_data = [
                data.datetime.date().strftime("%d/%m/%Y"),
                f"{data.user.lastname} {data.user.firstname}",
                data.node.company.name,
                data.node.type_label,
                get_node_label(data.node, with_details=True),
                "Validé" if data.status == "valid" else "Invalidé",
            ]
            writer.add_row(row_data)
        write_file_to_request(self.request, self.filename, writer.render())
        return self.request.response


class ValidationsManagementOdsView(ValidationsManagementXlsView):
    """
    Export du tableau de suivi des validations au format ODS
    """

    _factory = OdsExporter


def includeme(config):
    config.add_route("management_validations", "management/validations")
    config.add_route(
        "management_validations_export", "management/validations.{extension}"
    )
    config.add_view(
        ValidationsManagementView,
        route_name="management_validations",
        renderer="management/validations.mako",
        permission=PERMISSIONS["global.company_view_accounting"],
    )
    config.add_view(
        ValidationsManagementXlsView,
        route_name="management_validations_export",
        match_param="extension=xls",
        permission=PERMISSIONS["global.company_view_accounting"],
    )
    config.add_view(
        ValidationsManagementOdsView,
        route_name="management_validations_export",
        match_param="extension=ods",
        permission=PERMISSIONS["global.company_view_accounting"],
    )
    config.add_admin_menu(
        parent="management",
        order=0,
        label="Validations",
        href="/management/validations",
    )

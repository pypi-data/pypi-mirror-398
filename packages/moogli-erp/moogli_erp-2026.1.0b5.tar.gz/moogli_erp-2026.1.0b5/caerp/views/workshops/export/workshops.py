from typing import Any

from sqla_inspect.csv import CsvExporter
from sqla_inspect.excel import XlsExporter
from sqla_inspect.ods import OdsExporter

from caerp.models.activity import ATTENDANCE_STATUS
from caerp.models.workshop import (
    WorkshopTagOption,
    Workshop,
)
from caerp.utils.strings import format_account
from caerp.views import BaseCsvView
from caerp.views.workshops.export.mixins import (
    CaeWorkshopFilterMixin,
    CompanyWorkshopFilterMixin,
)
from caerp.views.workshops.lists import WorkshopListTools


def _status_key(status_value: str) -> str:
    return f"{status_value}_count"


def _attendance_summary(workshop: Workshop) -> dict[str, int]:
    """Sumarize the attendance of participants to a workshop

    Give the number of participants per-status.

    Summarize several timeslots. If a participant has a different status among timeslots, it will add up to
    "mixed_count" and to no other counter.

    Example return:

    {
        "registered_count": 0,
        "attended_count": 10,
        "excused_count": 2,
        "absent_count": 2"
        "mixed_count": 0,
    }
    """
    participations_statuses = {}

    status_stats = {}

    for value, _ in ATTENDANCE_STATUS + (("mixed", ""),):
        status_stats[_status_key(value)] = 0

    for timeslot in workshop.timeslots:
        for attendance in timeslot.attendances:
            if attendance.account_id not in participations_statuses:
                participations_statuses[attendance.account_id] = set()
            participations_statuses[attendance.account_id].add(attendance.status)

    for _, statuses in participations_statuses.items():
        if len(statuses) == 1:
            status_stats[_status_key(statuses.pop())] += 1
        else:
            status_stats["mixed_count"] += 1

    return status_stats


def get_base_workshop_fields_for_export(workshop: Workshop) -> dict[str, Any]:
    hours = sum(t.duration[0] for t in workshop.timeslots)
    minutes = sum(t.duration[1] for t in workshop.timeslots)

    duration = hours * 60 + minutes

    start_date = workshop.timeslots[0].start_time.date()

    (info1, info2, info3) = map(
        lambda info: None if info is None else info.label,
        [workshop.info1, workshop.info2, workshop.info3],
    )

    row = {
        "date": start_date,
        "label": workshop.name,
        "duration": duration,
        "info1": info1,
        "info2": info2,
        "info3": info3,
    }

    for tag in workshop.tags:
        row[tag.label] = "Oui"
    # Volontairement pas de "Non" pour alléger  la sortie.
    return row


def stream_workshop_entries_for_export(query) -> dict[str, Any]:
    for workshop in query.all():
        row = get_base_workshop_fields_for_export(workshop)
        row["name"] = ", ".join(format_account(i) for i in workshop.trainers)
        row["total_count"] = len(workshop.participants)
        row["multi_date"] = "Oui" if not workshop.relates_single_day() else ""

        attendance_summary = _attendance_summary(workshop)
        row.update(attendance_summary)

        yield row


class WorkshopWriterMixin:
    @property
    def headers(self):
        return (
            (
                {"name": "date", "label": "Date"},
                {"name": "multi_date", "label": "Multi-date"},
                {"name": "label", "label": "Intitulé"},
                {"name": "name", "label": "Nom animateur·ices"},
                {"name": "duration", "label": "Durée"},
                {"name": "total_count", "label": "Nb. total inscrit·es"},
            )
            + tuple(
                {"name": _status_key(value), "label": f"Nb. {label}"}
                for value, label in ATTENDANCE_STATUS
            )
            + (
                {"name": "mixed_count", "label": "Nb. partiellement présent"},
                {"name": "info1", "label": "Action 1"},
                {"name": "info2", "label": "Action 2"},
                {"name": "info3", "label": "Action 3"},
            )
            + tuple(
                {"name": i.label, "label": f"🏷️ {i.label}"}
                for i in WorkshopTagOption.query()
            )
        )


class WorkshopCsvWriter(WorkshopWriterMixin, CsvExporter):
    pass


class WorkshopXlsWriter(WorkshopWriterMixin, XlsExporter):
    pass


class WorkshopOdsWriter(WorkshopWriterMixin, OdsExporter):
    pass


class BaseWorkshopExportView(WorkshopListTools, BaseCsvView):
    def _init_writer(self):
        return self.writer()

    def _stream_rows(self, query):
        return stream_workshop_entries_for_export(query)


class WorkshopXlsView(BaseWorkshopExportView):
    writer = WorkshopXlsWriter
    filename = "ateliers.xlsx"


class WorkshopOdsView(BaseWorkshopExportView):
    writer = WorkshopOdsWriter
    filename = "ateliers.ods"


class WorkshopCsvView(BaseWorkshopExportView):
    writer = WorkshopCsvWriter
    filename = "ateliers.csv"


class CaeWorkshopXlsView(CaeWorkshopFilterMixin, BaseWorkshopExportView):
    writer = WorkshopXlsWriter
    filename = "ateliers.xlsx"


class CaeWorkshopOdsView(CaeWorkshopFilterMixin, BaseWorkshopExportView):
    writer = WorkshopOdsWriter
    filename = "ateliers.ods"


class CaeWorkshopCsvView(CaeWorkshopFilterMixin, BaseWorkshopExportView):
    writer = WorkshopCsvWriter
    filename = "ateliers.csv"


class CompanyWorkshopXlsView(CompanyWorkshopFilterMixin, BaseWorkshopExportView):
    writer = WorkshopXlsWriter
    filename = "ateliers.xlsx"


class CompanyWorkshopOdsView(CompanyWorkshopFilterMixin, BaseWorkshopExportView):
    writer = WorkshopXlsWriter
    filename = "ateliers.xlsx"


class CompanyWorkshopCsvView(CompanyWorkshopFilterMixin, BaseWorkshopExportView):
    writer = WorkshopCsvWriter
    filename = "ateliers.csv"

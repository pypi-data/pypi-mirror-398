from sqla_inspect.csv import CsvExporter
from sqla_inspect.excel import XlsExporter
from sqla_inspect.ods import OdsExporter

from caerp.models.workshop import WorkshopTagOption
from caerp.utils.strings import format_account
from caerp.views import BaseCsvView
from caerp.views.workshops.export.mixins import (
    CaeWorkshopFilterMixin,
    CompanyWorkshopFilterMixin,
)
from caerp.views.workshops.export.workshops import get_base_workshop_fields_for_export
from caerp.views.workshops.lists import WorkshopListTools


class WorkshopParticipantsWriterMixin:
    @property
    def headers(self):
        base_headers = (
            {"name": "date", "label": "Date"},
            {"name": "label", "label": "Intitulé"},
            {"name": "name", "label": "Nom"},
            {"name": "role", "label": "Rôle"},
            {"name": "duration", "label": "Durée"},
            {"name": "attended", "label": "Participation"},
            {"name": "info1", "label": "Action 1"},
            {"name": "info2", "label": "Action 2"},
            {"name": "info3", "label": "Action 3"},
        )
        return base_headers + tuple(
            {"name": i.label, "label": f"🏷️ {i.label}"}
            for i in WorkshopTagOption.query()
        )


class WorkshopParticipantsCsvWriter(WorkshopParticipantsWriterMixin, CsvExporter):
    pass


class WorkshopParticipantsXlsWriter(WorkshopParticipantsWriterMixin, XlsExporter):
    pass


class WorkshopParticipantsOdsWriter(WorkshopParticipantsWriterMixin, OdsExporter):
    pass


def stream_workshop_participants_entries_for_export(query):
    """
    Stream workshop datas for csv export
    """
    for workshop in query.all():
        workshop_base_row = get_base_workshop_fields_for_export(workshop)

        for participant in workshop.participants:
            attended = False
            for timeslot in workshop.timeslots:
                if timeslot.user_status(participant.id) == "Présent":
                    attended = True
                    break
            row = workshop_base_row.copy()
            participant_fields = {
                "name": format_account(participant),
                "role": "apprenant",
                "attended": "Oui" if attended else "Non",
            }
            row.update(participant_fields.items())
            yield row

        for trainer in workshop.trainers:
            row = workshop_base_row.copy()
            trainer_fields = {
                "name": format_account(trainer),
                "role": "formateur",
            }
            row.update(trainer_fields.items())
            yield row


class BaseWorkshopParticipantsExportView(WorkshopListTools, BaseCsvView):
    def _init_writer(self):
        return self.writer()

    def _stream_rows(self, query):
        return stream_workshop_participants_entries_for_export(query)


class CaeWorkshopParticipantsCsvView(
    CaeWorkshopFilterMixin,
    BaseWorkshopParticipantsExportView,
):
    writer = WorkshopParticipantsCsvWriter
    filename = "participants_ateliers.csv"


class CompanyWorkshopParticipantsCsvView(
    CompanyWorkshopFilterMixin,
    BaseWorkshopParticipantsExportView,
):
    writer = WorkshopParticipantsCsvWriter
    filename = "participants_ateliers.csv"


class WorkshopParticipantsXlsView(BaseWorkshopParticipantsExportView):
    writer = WorkshopParticipantsXlsWriter
    filename = "participants_ateliers.xlsx"


class CaeWorkshopParticipantsXlsView(
    CaeWorkshopFilterMixin,
    BaseWorkshopParticipantsExportView,
):
    writer = WorkshopParticipantsXlsWriter
    filename = "participants_ateliers.xlsx"


class CompanyWorkshopParticipantsXlsView(
    CaeWorkshopFilterMixin,
    BaseWorkshopParticipantsExportView,
):
    writer = WorkshopParticipantsXlsWriter
    filename = "participants_ateliers.xlsx"


class WorkshopParticipantsOdsView(BaseWorkshopParticipantsExportView):
    writer = WorkshopParticipantsOdsWriter
    filename = "participants_ateliers.ods"


class CaeWorkshopParticipantsOdsView(
    CaeWorkshopFilterMixin,
    BaseWorkshopParticipantsExportView,
):
    writer = WorkshopParticipantsOdsWriter
    filename = "participants_ateliers.ods"


class CompanyWorkshopParticipantsOdsView(
    CompanyWorkshopFilterMixin,
    BaseWorkshopParticipantsExportView,
):
    writer = WorkshopParticipantsOdsWriter
    filename = "participants_ateliers.ods"


class WorkshopParticipantsCsvView(BaseWorkshopParticipantsExportView):
    writer = WorkshopParticipantsCsvWriter
    filename = "participants_ateliers.csv"

from caerp.consts.permissions import PERMISSIONS
from caerp.views.workshops.export.participants import (
    WorkshopParticipantsCsvView,
    WorkshopParticipantsXlsView,
    WorkshopParticipantsOdsView,
    CaeWorkshopParticipantsCsvView,
    CaeWorkshopParticipantsXlsView,
    CaeWorkshopParticipantsOdsView,
    CompanyWorkshopParticipantsCsvView,
    CompanyWorkshopParticipantsXlsView,
    CompanyWorkshopParticipantsOdsView,
)
from caerp.views.workshops.export.workshops import (
    WorkshopCsvView,
    WorkshopXlsView,
    WorkshopOdsView,
    CaeWorkshopCsvView,
    CaeWorkshopXlsView,
    CaeWorkshopOdsView,
    CompanyWorkshopCsvView,
    CompanyWorkshopXlsView,
    CompanyWorkshopOdsView,
)


def includeme(config):
    for view, route_base_name, file_format in [
        (WorkshopParticipantsCsvView, "workshops_participants", "csv"),
        (WorkshopParticipantsXlsView, "workshops_participants", "xlsx"),
        (WorkshopParticipantsOdsView, "workshops_participants", "ods"),
        (CaeWorkshopParticipantsCsvView, "cae_workshops_participants", "csv"),
        (CaeWorkshopParticipantsXlsView, "cae_workshops_participants", "xlsx"),
        (CaeWorkshopParticipantsOdsView, "cae_workshops_participants", "ods"),
        (CompanyWorkshopParticipantsCsvView, "company_workshops_participants", "csv"),
        (CompanyWorkshopParticipantsXlsView, "company_workshops_participants", "xlsx"),
        (CompanyWorkshopParticipantsOdsView, "company_workshops_participants", "ods"),
        (WorkshopCsvView, "workshops", "csv"),
        (WorkshopXlsView, "workshops", "xlsx"),
        (WorkshopOdsView, "workshops", "ods"),
        (CaeWorkshopCsvView, "cae_workshops", "csv"),
        (CaeWorkshopXlsView, "cae_workshops", "xlsx"),
        (CaeWorkshopOdsView, "cae_workshops", "ods"),
        (CompanyWorkshopCsvView, "company_workshops", "csv"),
        (CompanyWorkshopXlsView, "company_workshops", "xlsx"),
        (CompanyWorkshopOdsView, "company_workshops", "ods"),
    ]:
        config.add_view(
            view,
            route_name=route_base_name + "{file_format}",
            match_param=f"file_format=.{file_format}",
            permission=PERMISSIONS["global.manage_workshop"],
        )

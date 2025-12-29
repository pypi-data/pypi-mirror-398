"""
Panel listant les nouveautés de la dernière version
"""
import json

from caerp.utils.sys_environment import resource_filename


def manage_dashboard_release_notes_panel(context, request):
    last_version_resume = None
    last_version_resume_es = None
    release_notes_filepath = resource_filename("static/release_notes.json")
    with open(release_notes_filepath) as release_notes_file:
        data = json.load(release_notes_file)
    release_notes = data["release_notes"]
    for version in release_notes:
        if "resume" in version and not last_version_resume:
            last_version_resume = version["resume"]
        if "resume_es" in version and not last_version_resume_es:
            last_version_resume_es = version["resume_es"]
    return {
        "last_version_resume": last_version_resume,
        "last_version_resume_es": last_version_resume_es,
    }


def includeme(config):
    config.add_panel(
        manage_dashboard_release_notes_panel,
        "manage_dashboard_release_notes",
        renderer="caerp:templates/panels/manage" "/manage_dashboard_release_notes.mako",
    )

    config.add_panel(
        manage_dashboard_release_notes_panel,
        "manage_dashboard_release_notes_es",
        renderer="caerp:templates/panels/manage"
        "/manage_dashboard_release_notes_es.mako",
    )

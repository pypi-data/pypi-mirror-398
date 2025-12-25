"""
Various functions used by Configure sub-application
"""

import re

import pandas as pd

from ositah.apps.configuration.parameters import (
    PROJECT_MGT_PROJECT_TYPE_DISABLED,
    PROJECT_MGT_PROJECT_TYPE_LOCAL,
)
from ositah.utils.projects import (
    MASTERPROJECT_DELETED_ACTIVITY,
    MASTERPROJECT_LOCAL_PROJECT,
    get_all_hito_activities,
)


def list_box_empty(list_options):
    """
    Check if the options of the list box contains only one entry corresponding to a
    placeholder item.

    :param team_list_items: options of a list box
    :return: boolean (true if only a placeholder entry is present)
    """

    if (
        len(list_options) == 1
        and list_options[0]["label"] is None
        and list_options[0]["value"] is None
    ):
        return True
    else:
        return False


def get_masterprojects_items(project_activity, category: int = None) -> list:
    """
    Build the item list for masterprojects to be displayed in a select compoenent

    :param project_activity: True if it is a project rather than a Hito activity
    :param category: one of PROJECT_MGT_PROJECT_TYPE_xxx values or None. If None, menas
                     all active (non disabled) projects/activities
    :return: list of projects/activities
    """

    if category == PROJECT_MGT_PROJECT_TYPE_LOCAL:
        # Local projects have no masterproject
        return []

    activities = get_all_hito_activities(project_activity)
    masterproject_items = []
    if category == PROJECT_MGT_PROJECT_TYPE_DISABLED:
        disabled = pd.DataFrame()
        disabled[["masterproject_real", "project_real"]] = activities[
            activities.masterproject == MASTERPROJECT_DELETED_ACTIVITY
        ]["project"].str.split(" / ", n=1, expand=True)
        for masterproject in sorted(
            disabled["masterproject_real"].unique(),
            key=lambda x: x.upper(),
        ):
            masterproject_items.append({"label": masterproject, "value": masterproject})
    else:
        masterproject_items = sorted(
            activities[
                (activities.masterproject != MASTERPROJECT_DELETED_ACTIVITY)
                & (activities.masterproject != MASTERPROJECT_LOCAL_PROJECT)
            ]["masterproject"].unique(),
            key=lambda x: x.upper(),
        )

    return masterproject_items


def get_projects_items(masterproject, project_activity, category: int = None) -> list:
    """
    Build the item list for projects to be displayed in a select compoenent

    :param masterproject: selected master project
    :param project_activity: True if it is a project rather than a Hito activity
    :param category: one of PROJECT_MGT_PROJECT_TYPE_xxx values or None. If None, menas
                     all active (non disabled) projects/activities
    :return: list of projects/activities
    """

    if category == PROJECT_MGT_PROJECT_TYPE_LOCAL:
        project_prefix = masterproject
        masterproject = MASTERPROJECT_LOCAL_PROJECT
    elif category == PROJECT_MGT_PROJECT_TYPE_DISABLED:
        project_prefix = masterproject
        masterproject = MASTERPROJECT_DELETED_ACTIVITY
    else:
        project_prefix = None

    if masterproject:
        activities = get_all_hito_activities(project_activity)
        project_items = []
        for project in sorted(
            activities[activities.masterproject == masterproject]["project"].unique(),
            key=lambda x: x.upper(),
        ):
            if project_prefix is None or re.match(rf"{project_prefix}", project):
                if category == PROJECT_MGT_PROJECT_TYPE_DISABLED:
                    project_name = project.split("/")[1]
                else:
                    project_name = project
                project_items.append({"label": project_name, "value": project})
        return project_items
    else:
        return []

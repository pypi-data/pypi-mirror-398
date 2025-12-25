"""
Dash callbacks for Configuration applications
"""

from datetime import datetime
from typing import Any, List

import dash_bootstrap_components as dbc
from dash import callback_context, html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from ositah.app import app
from ositah.apps.configuration.parameters import *
from ositah.apps.configuration.tools import (
    get_masterprojects_items,
    get_projects_items,
    list_box_empty,
)
from ositah.utils.exceptions import InvalidCallbackInput
from ositah.utils.menus import TABLE_TYPE_TABLE, GlobalParams
from ositah.utils.period import get_declaration_periods
from ositah.utils.projects import (
    MASTERPROJECT_DELETED_ACTIVITY,
    NSIP_CLASS_OTHER_ACTIVITY,
    NSIP_CLASS_PROJECT,
    add_activity,
    add_activity_teams,
    get_all_hito_activities,
    get_hito_nsip_activities,
    get_nsip_activities,
    nsip_activity_name_id,
    ositah2hito_project_name,
    reenable_activity,
    remove_activity,
    remove_activity_teams,
    update_activity_name,
)
from ositah.utils.teams import get_project_team_ids


def check_activity_changes(project_activity: bool):
    """
    Retrieve the list of activity changes in NSIP compared to the Hito projects

    :param project_activity: true for projects, false for other activities
    :return: dataframe with changed activities
    """

    nsip_activities = get_nsip_activities(project_activity)
    if nsip_activities is None or nsip_activities.empty:
        raise PreventUpdate

    hito_projects = get_hito_nsip_activities(project_activity)

    if project_activity:
        merge_left_attr = "nsip_project_id"
    else:
        merge_left_attr = "nsip_reference_id"
    activity_changes = hito_projects.merge(
        nsip_activities,
        how="outer",
        left_on=merge_left_attr,
        right_on="id",
        indicator=True,
        suffixes=[None, "_nsip"],
    )
    activity_changes["status"] = None
    activity_changes.loc[activity_changes._merge == "left_only", "status"] = PROJECT_CHANGE_REMOVED
    activity_changes.loc[activity_changes._merge == "right_only", "status"] = PROJECT_CHANGE_ADDED
    activity_changes.loc[
        (activity_changes._merge == "both")
        & (
            (activity_changes.nsip_project != activity_changes.ositah_name)
            | (activity_changes["master_project.name"] != activity_changes.nsip_master)
        ),
        "status",
    ] = PROJECT_CHANGE_CHANGED
    activity_changes.drop(activity_changes[activity_changes.status.isna()].index, inplace=True)

    # Set NaN to 0 in referentiel_id and id_nsip as np.NaN is a float and prevent casting to int.
    activity_changes.loc[activity_changes["referentiel_id"].isna(), "referentiel_id"] = 0
    activity_changes.loc[activity_changes["id_nsip"].isna(), "id_nsip"] = 0
    activity_changes["referentiel_id"] = activity_changes.referentiel_id.astype(int)
    activity_changes["id_nsip"] = activity_changes.id_nsip.astype(int)

    return activity_changes


@app.callback(
    Output(TAB_ID_ACTIVITY_TEAMS, "children"),
    Output(TAB_ID_NSIP_PROJECT_SYNC, "children"),
    Output(TAB_ID_DECLARATION_PERIODS, "children"),
    Output(TAB_ID_PROJECT_MGT, "children"),
    Input(CONFIGURATION_TAB_MENU_ID, "active_tab"),
)
def display_tab_content(active_tab):
    from ositah.apps.configuration.main import (
        declaration_periods_layout,
        nsip_sync_layout,
        project_mgt_layout,
        project_teams_layout,
    )

    if active_tab == TAB_ID_ACTIVITY_TEAMS:
        return project_teams_layout(), "", "", ""
    elif active_tab == TAB_ID_NSIP_PROJECT_SYNC:
        return "", nsip_sync_layout(), "", ""
    elif active_tab == TAB_ID_DECLARATION_PERIODS:
        return "", "", declaration_periods_layout(), ""
    elif active_tab == TAB_ID_PROJECT_MGT:
        return "", "", "", project_mgt_layout()
    else:
        return "", "", "", ""


@app.callback(
    Output(NSIP_SYNC_CONTENT_ID, "children"),
    Output(NSIP_SYNC_APPLY_DIFF_ID, "disabled"),
    Input(NSIP_SYNC_SHOW_DIFF_ID, "n_clicks"),
    Input(NSIP_SYNC_APPLY_DIFF_ID, "n_clicks"),
    State(NSIP_SYNC_ACTIVITY_TYPE_ID, "value"),
    prevent_initial_call=True,
)
def show_nsip_activity_differences(_, __, activity_type):
    """
    Handle buttons from the NSIP synchronisation tab. Values of input parameters are not used.
    Do nothing if no button was clicked.

    :param activity_type: type of NSIP activity (integer)
    :return: contents of NSIP_SYNC_CONTENT_ID components
    """

    global_params = GlobalParams()

    if not callback_context.triggered:
        return PreventUpdate
    else:
        button_id = callback_context.triggered[0]["prop_id"].split(".")[0]

    if activity_type == NSIP_SYNC_ACTIVITY_TYPE_PROJECT:
        project_activity = True
    else:
        project_activity = False

    activity_changes = check_activity_changes(project_activity)

    if button_id == NSIP_SYNC_SHOW_DIFF_ID:
        add_num = len(activity_changes[activity_changes.status == PROJECT_CHANGE_ADDED])
        change_num = len(activity_changes[activity_changes.status == PROJECT_CHANGE_CHANGED])
        remove_num = len(activity_changes[activity_changes.status == PROJECT_CHANGE_REMOVED])
        total_changes = add_num + change_num + remove_num

        if add_num or change_num or remove_num:
            data_columns = {
                # TO BE FIXED: Column names (nsip_master, nsip_project, ositah_name)
                # are misleading...
                "Masterprojet OSITAH": "nsip_master",
                "Projet OSITAH": "nsip_project",
                "ID OSITAH": "id",
                "ID Référentiel": "referentiel_id",
                "Masterprojet NSIP": "master_project.name",
                "Projet NSIP": "ositah_name",
                "ID NSIP": "id_nsip",
                "Statut": "status",
            }
            theader = [html.Thead(html.Tr([html.Th(c) for c in data_columns.keys()]))]

            tbody = [
                html.Tbody(
                    [
                        html.Tr([html.Td(row[c]) for c in data_columns.values()])
                        for i, row in activity_changes.sort_values(
                            by=["nsip_master", "nsip_project"]
                        ).iterrows()
                    ]
                )
            ]

            table = dbc.Table(
                theader + tbody,
                id={"type": TABLE_TYPE_TABLE, "id": TABLE_NSIP_PROJECT_SYNC_ID},
                bordered=True,
                hover=True,
                striped=True,
                class_name="sortable",
            )

            summary_msg = html.B(
                (
                    f"{total_changes} changements NSIP / OSITAH : {add_num} additions,"
                    f" {remove_num} suppressions, {change_num} modifications"
                )
            )

            apply_button_disabled = False

        else:
            table = html.Div()
            if project_activity:
                summary_msg = "Les projets NSIP et OSITAH sont synchronisés"
            else:
                summary_msg = "Les activités NSIP et OSITAH sont synchronisées"
            apply_button_disabled = True

        return (
            html.Div(
                [
                    dbc.Alert(summary_msg),
                    html.P(),
                    table,
                ]
            ),
            apply_button_disabled,
        )

    elif button_id == NSIP_SYNC_APPLY_DIFF_ID:
        add_failed = {}
        change_failed = {}
        delete_failed = {}

        for _, activity in activity_changes[
            activity_changes.status == PROJECT_CHANGE_CHANGED
        ].iterrows():
            status, error_msg = update_activity_name(
                activity.id,
                activity.referentiel_id,
                activity.id_nsip,
                activity["master_project.name"],
                activity.ositah_name,
            )
            if status:
                change_failed[f"{activity['nsip_name_id']}"] = error_msg

        for _, activity in activity_changes[
            activity_changes.status == PROJECT_CHANGE_ADDED
        ].iterrows():
            activity_full_name = ositah2hito_project_name(
                activity["master_project.name"], activity.ositah_name
            )
            activity_teams = get_project_team_ids(global_params.project_teams, activity_full_name)
            status, error_msg = add_activity(
                activity.id_nsip,
                activity["master_project.name"],
                activity.ositah_name,
                activity_teams,
                project_activity,
            )
            if status:
                add_failed[
                    (
                        f"{activity['master_project.name']} / {activity.ositah_name}"
                        f" (NSIP ID: {activity.id_nsip})"
                    )
                ] = error_msg

        for _, activity in activity_changes[
            activity_changes.status == PROJECT_CHANGE_REMOVED
        ].iterrows():
            _, _, project_id, reference_id = nsip_activity_name_id(
                activity.nsip_name_id,
                NSIP_CLASS_PROJECT if project_activity else NSIP_CLASS_OTHER_ACTIVITY,
            )
            if project_activity:
                nsip_id = project_id
            else:
                nsip_id = reference_id
            status, error_msg = remove_activity(
                activity.id, activity.referentiel_id, nsip_id, project_activity
            )
            if status:
                delete_failed[f"{activity['nsip_name_id']}"] = error_msg

        if (
            len(change_failed.keys()) == 0
            and len(add_failed.keys()) == 0
            and len(delete_failed) == 0
        ):
            return dbc.Alert("All changes applied successfully to Hito"), True
        else:
            alert_msg = []
            if len(change_failed.keys()) > 0:
                alert_msg.append(
                    html.P(html.B("Erreur durant la mise à jour des activités suivantes :"))
                )
                alert_msg.append(html.Ul([html.Li(f"{k}: {v}") for k, v in change_failed.items()]))
            if len(add_failed.keys()) > 0:
                alert_msg.append(html.P(html.B("Erreur durant l'ajout des activités suivantes :")))
                alert_msg.append(html.Ul([html.Li(f"{k}: {v}") for k, v in add_failed.items()]))
            if len(delete_failed.keys()) > 0:
                alert_msg.append(
                    html.P(html.B("Erreur durant la suppression des activités suivantes :"))
                )
                alert_msg.append(html.Ul([html.Li(f"{k}: {v}") for k, v in delete_failed.items()]))
            return dbc.Alert(alert_msg), True

    else:
        return dbc.Alert("Bouton invalide", color="danger"), True


@app.callback(
    Output(ACTIVITY_TEAMS_PROJECTS_ID, "options"),
    Output(ACTIVITY_TEAMS_PROJECTS_ID, "value"),
    Input(ACTIVITY_TEAMS_MASTERPROJECTS_ID, "value"),
    State(ACTIVITY_TEAMS_PROJECT_ACTIVITY_ID, "data"),
    prevent_initial_call=True,
)
def activity_team_projects(masterproject, project_activity):
    """
    Display the list of projects associated with the selected masterproject in the project
    list box. Also reset the project selected value.

    :param masterproject: selected master project
    :param project_activity: True if it is a project rather than a Hito activity
    :return: list box options
    """

    items = get_projects_items(masterproject, project_activity, None)
    if len(items):
        return items, None
    else:
        return [], None


@app.callback(
    Output(PROJECT_MGT_MASTERPROJECT_LIST_ID, "options"),
    Output(PROJECT_MGT_MASTERPROJECT_LIST_ID, "value"),
    Input(PROJECT_MGT_PROJECT_TYPE_ID, "value"),
    State(PROJECT_MGT_PROJECT_ACTIVITY_ID, "data"),
    prevent_initial_call=True,
)
def project_mgt_masterprojects(category, project_activity):
    """
    Display the list of projects associated with the selected masterproject in the project
    list box. Also reset the masterproject selected value.

    :param category: a number indicating if NSIP, local or disabled projects must be displayed
    :param project_activity: True if it is a project rather than a Hito activity
    :return: list box options, selected value reset to an empty string
    """

    if category is None:
        return [], ""
    else:
        items = get_masterprojects_items(project_activity, category)
        return items, ""


@app.callback(
    Output(PROJECT_MGT_PROJECT_LIST_ID, "options"),
    Output(PROJECT_MGT_PROJECT_LIST_ID, "value"),
    Input(PROJECT_MGT_MASTERPROJECT_LIST_ID, "value"),
    Input(PROJECT_MGT_PROJECT_TYPE_ID, "value"),
    State(PROJECT_MGT_PROJECT_ACTIVITY_ID, "data"),
    prevent_initial_call=True,
)
def project_mgt_projects(masterproject, category, project_activity):
    """
    Display the list of projects associated with the selected masterproject in the project
    list box. If local projects are selected, the masterproject value is empty.
    Also reset the project selected value.

    :param masterproject: selected master project
    :param category: a number indicating if NSIP, local or disabled projects must be displayed
    :param project_activity: True if it is a project rather than a Hito activity
    :return: list box options
    """

    if masterproject or category == PROJECT_MGT_PROJECT_TYPE_LOCAL:
        items = get_projects_items(masterproject, project_activity, category)
        return items, ""
    else:
        return [], ""


@app.callback(
    Output(PROJECT_MGT_ACTION_BUTTON_ID, "children"),
    Output(PROJECT_MGT_ACTION_BUTTON_ID, "style"),
    Output(PROJECT_MGT_ACTION_BUTTON_ID, "disabled"),
    Input(PROJECT_MGT_PROJECT_LIST_ID, "value"),
    State(PROJECT_MGT_PROJECT_TYPE_ID, "value"),
    prevent_initial_call=True,
)
def project_mgt_enable_action(activity, category):
    """
    If a project has been selected, enable the button with the appropriate action depending on
    activity type. If no project is elected, hide and disable the action button.

    :param activity: name of the selected activity
    :param category: whether the project is a local project, a NSIP project or a disabled one
    """

    if activity:
        if category == PROJECT_MGT_PROJECT_TYPE_DISABLED:
            action = PROJECT_MGT_ACTION_BUTTON_ENABLE
        else:
            action = PROJECT_MGT_ACTION_BUTTON_DISABLE
        return action, {"visibility": "visible"}, False
    else:
        return "", {"visibility": "hidden"}, True


@app.callback(
    Output(PROJECT_MGT_STATUS_ID, "is_open"),
    Output(PROJECT_MGT_STATUS_ID, "children"),
    Output(PROJECT_MGT_STATUS_ID, "color"),
    Input(PROJECT_MGT_ACTION_BUTTON_ID, "n_clicks"),
    State(PROJECT_MGT_ACTION_BUTTON_ID, "children"),
    State(PROJECT_MGT_PROJECT_LIST_ID, "value"),
    State(PROJECT_MGT_PROJECT_ACTIVITY_ID, "data"),
    prevent_initial_call=True,
)
def project_mgt_execute_action(n_clicks, action, activity, is_project):
    """
    Execute action associated with the button. Actual action is retrieved from the
    button label.

    :param n_clicks: number of clicks, ignored
    :param action: the button label
    :param activity: name of the project/activity
    :param is_project: true if a project, false if is an Hito activity
    :return: status message and color
    """

    if action == PROJECT_MGT_ACTION_BUTTON_DISABLE:
        return True, "Désactivation projet : pas encore implémentée", "warning"
    elif action == PROJECT_MGT_ACTION_BUTTON_ENABLE:
        status, status_msg = reenable_activity(activity, is_project, MASTERPROJECT_DELETED_ACTIVITY)
        if status == 0:
            return True, f"Projet {activity} réactivé avec succès", "success"
        else:
            alert_msg = html.Div(
                html.P(f"Erreur durant la réactivation du projet {activity}"), html.P(error_msg)
            )
            return True, alert_msg, "danger"
    else:
        return True, f"Internal error: invalid action ({action})", "danger"


@app.callback(
    Output(ACTIVITY_TEAMS_LAB_TEAMS_ID, "options"),
    Input(ACTIVITY_TEAMS_PROJECTS_ID, "value"),
    State(ACTIVITY_TEAMS_MASTERPROJECTS_ID, "value"),
    prevent_initial_call=True,
)
def display_teams(project, masterproject):
    """
    Display the Hito teams not yet associated with the selected project in the lab team
    list box

    :param project: selected project
    :param masterproject: selected master project
    :return: list box options for lab teams
    """

    global_params = GlobalParams()
    session_data = global_params.session_data

    if masterproject and project:
        lab_team_items = []
        for team in sorted(session_data.agent_teams):
            lab_team_items.append({"label": team, "value": team})
        return lab_team_items

    else:
        return []


@app.callback(
    Output(ACTIVITY_TEAMS_BUTTON_ADD_ID, "disabled"),
    Input(ACTIVITY_TEAMS_LAB_TEAMS_ID, "value"),
)
def enable_team_update_buttons(selected_team):
    """
    Enable the button allowing to add the selected team in lab teams into the project teams

    :param selected_team: selected lab team
    :return: boolean
    """
    if selected_team:
        return False
    else:
        return True


@app.callback(
    Output(ACTIVITY_TEAMS_BUTTON_REMOVE_ID, "disabled"),
    Input(ACTIVITY_TEAMS_SELECTED_TEAMS_ID, "value"),
)
def enable_team_remove_buttons(selected_team):
    """
    Enable the button allowing to remove a team from the project teams

    :param selected_team: selected lab team
    :return: boolean
    """
    if selected_team:
        return False
    else:
        return True


@app.callback(
    Output(ACTIVITY_TEAMS_SELECTED_TEAMS_ID, "options"),
    Output(ACTIVITY_TEAMS_ADDED_TEAMS_ID, "data"),
    Output(ACTIVITY_TEAMS_REMOVED_TEAMS_ID, "data"),
    Output(ACTIVITY_TEAMS_BUTTON_UPDATE_ID, "disabled"),
    Output(ACTIVITY_TEAMS_BUTTON_CANCEL_ID, "disabled"),
    Output(ACTIVITY_TEAMS_LAB_TEAMS_ID, "value"),
    Output(ACTIVITY_TEAMS_SELECTED_TEAMS_ID, "value"),
    Input(ACTIVITY_TEAMS_BUTTON_ADD_ID, "n_clicks"),
    Input(ACTIVITY_TEAMS_BUTTON_REMOVE_ID, "n_clicks"),
    Input(ACTIVITY_TEAMS_PROJECTS_ID, "value"),
    State(ACTIVITY_TEAMS_MASTERPROJECTS_ID, "value"),
    State(ACTIVITY_TEAMS_LAB_TEAMS_ID, "value"),
    State(ACTIVITY_TEAMS_SELECTED_TEAMS_ID, "options"),
    State(ACTIVITY_TEAMS_SELECTED_TEAMS_ID, "value"),
    State(ACTIVITY_TEAMS_PROJECT_ACTIVITY_ID, "data"),
    State(ACTIVITY_TEAMS_ADDED_TEAMS_ID, "data"),
    State(ACTIVITY_TEAMS_REMOVED_TEAMS_ID, "data"),
    prevent_initial_call=True,
)
def update_selected_teams(
    update_n_click: int,
    cancel_n_click: int,
    project,
    masterproject,
    selected_lab_team,
    team_list_items,
    selected_activity_team,
    project_activity,
    added_teams,
    removed_teams,
):
    """
    Update the project teams list box after a project selection change or a lab team
    selection.

    :param update_n_click: clicks (ignored) for update button
    :param cancel_n_click: clicks (ignored) for cancel button
    :param project: selected project
    :param masterproject: selected masterproject
    :param selected_lab_team: selected team in lab teams (for addition)
    :param team_list_items: current contents of project teams list box
    :param selected_lab_team: selected team in project teams (for removal)
    :param project_activity: True if it is a project rather than a Hito activity
    :param added_teams: list of teams to be added
    :param removed_teams: list of teams to be removed
    :return: list box options for project teams and update/cancel buttons
    """

    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    else:
        active_input = ctx.triggered[0]["prop_id"].split(".")[0]

    # Selected project changed: reset the list to project teams
    if active_input == ACTIVITY_TEAMS_PROJECTS_ID:
        global_params = GlobalParams()
        session_data = global_params.session_data
        activities = get_all_hito_activities(project_activity)
        activity_teams = activities[
            (activities.masterproject == masterproject) & (activities.project == project)
        ]["team_name"]
        team_list_items = []
        for team in sorted(activity_teams):
            team_disabled = False if team in session_data.agent_teams else True
            team_list_items.append({"label": team, "value": team, "disabled": team_disabled})
        return team_list_items, [], [], True, True, None, None

    # A team being added to the project
    elif active_input == ACTIVITY_TEAMS_BUTTON_ADD_ID:
        team_present = False
        if team_list_items and not list_box_empty(team_list_items):
            for item in team_list_items:
                if item["value"] == selected_lab_team:
                    team_present = True
                    break
        else:
            team_list_items = []
        if team_present:
            raise PreventUpdate
        else:
            if selected_lab_team in removed_teams:
                removed_teams.remove(selected_lab_team)
            added_teams.append(selected_lab_team)
            team_list_items.append(
                {
                    "label": selected_lab_team,
                    "value": selected_lab_team,
                    "disabled": False,
                }
            )
            return (
                sorted(team_list_items, key=lambda x: x["label"]),
                added_teams,
                removed_teams,
                False,
                False,
                None,
                None,
            )

    elif active_input == ACTIVITY_TEAMS_BUTTON_REMOVE_ID:
        if team_list_items and not list_box_empty(team_list_items):
            team_list_items.remove(
                {
                    "label": selected_activity_team,
                    "value": selected_activity_team,
                    "disabled": False,
                }
            )
            removed_teams.append(selected_activity_team)
            if selected_activity_team in added_teams:
                added_teams.remove(selected_activity_team)
            return (
                sorted(team_list_items, key=lambda x: x["label"]),
                added_teams,
                removed_teams,
                False,
                False,
                None,
                None,
            )

        # Should not happen...
        else:
            raise PreventUpdate

    else:
        raise InvalidCallbackInput(active_input)


@app.callback(
    Output(ACTIVITY_TEAMS_STATUS_ID, "children"),
    Output(ACTIVITY_TEAMS_STATUS_ID, "is_open"),
    Output(ACTIVITY_TEAMS_STATUS_ID, "color"),
    Output(ACTIVITY_TEAMS_RESET_INDICATOR_ID, "data"),
    Input(ACTIVITY_TEAMS_BUTTON_UPDATE_ID, "n_clicks"),
    Input(ACTIVITY_TEAMS_BUTTON_CANCEL_ID, "n_clicks"),
    State(ACTIVITY_TEAMS_MASTERPROJECTS_ID, "value"),
    State(ACTIVITY_TEAMS_PROJECTS_ID, "value"),
    State(ACTIVITY_TEAMS_ADDED_TEAMS_ID, "data"),
    State(ACTIVITY_TEAMS_REMOVED_TEAMS_ID, "data"),
    State(ACTIVITY_TEAMS_PROJECT_ACTIVITY_ID, "data"),
    State(ACTIVITY_TEAMS_RESET_INDICATOR_ID, "data"),
    prevent_initial_call=True,
)
def update_activity_teams(
    update_n_click: int,
    cancel_n_click: int,
    masterproject: str,
    project: str,
    added_teams: List[str],
    removed_teams: List[str],
    project_activity: bool,
    reset_indicator: int,
):
    """
    Update the team list associated with the selected activity and if successful, reset the
    page elements (increment the reset indicator). Also clear the activity cache to force
    updating it from the database. This callback is also used to cancel the current
    modifications if the cancel button is clicked.

    :param update_n_click: clicks (ignored) for update button
    :param cancel_n_click: clicks (ignored) for cancel button
    :param masterproject: selected masterproject
    :param project: selected project
    :param added_teams: list of teams to add to the selected project
    :param removed_teams: list of teams to remove from the selected project
    :param project_activity: if true, an Hito project else an Hito activity
    :return: status msg, its color and the flag to reset the page elements
    """

    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    else:
        active_input = ctx.triggered[0]["prop_id"].split(".")[0]

    global_params = GlobalParams()
    session_data = global_params.session_data

    if active_input == ACTIVITY_TEAMS_BUTTON_CANCEL_ID:
        return "", False, "success", reset_indicator + 1
    else:
        status_msg = []
        status = 0

        if len(added_teams):
            add_status, add_status_msg = add_activity_teams(
                masterproject, project, added_teams, project_activity
            )
            status += add_status
            if add_status == 0:
                status_msg.append(
                    html.Div(
                        f"'{masterproject}/{project}' team list updated:"
                        f" '{', '.join(added_teams)}' added"
                    )
                )
            else:
                status_msg.append(
                    html.Div(
                        f"Failed to add '{', '.join(added_teams)}' to '{masterproject}/{project}'"
                        f" team list: {add_status_msg}",
                    )
                )

        if len(removed_teams):
            remove_status, remove_status_msg = remove_activity_teams(
                masterproject, project, removed_teams, project_activity
            )
            status += remove_status
            if remove_status == 0:
                status_msg.append(
                    html.Div(
                        f"'{masterproject}/{project}' team list updated:"
                        f" '{', '.join(removed_teams)}' removed"
                    )
                )
            else:
                status_msg.append(
                    html.Div(
                        f"Failed to remove '{', '.join(added_teams)}' from "
                        f"'{masterproject}/{project}' team list: {remove_status_msg}",
                    )
                )

        session_data.set_hito_activities(None, project_activity)

        if status == 0:
            status_color = "success"
        else:
            status_color = "danger"

        return (
            status_msg,
            True,
            status_color,
            reset_indicator + 1,
        )


@app.callback(
    Output(ACTIVITY_TEAMS_MASTERPROJECTS_ID, "value"),
    Input(ACTIVITY_TEAMS_RESET_INDICATOR_ID, "data"),
    prevent_initial_call=True,
)
def reset_mastproject_selection(_):
    """
    Reset the masterprojet selection to None after the teams for the currently selected
    project has been successfully updated.

    :param _: reset indicator (value not used)
    :return: masterproject selection
    """
    return None


@app.callback(
    Output(DECLARATION_PERIOD_NAME_ID, "value"),
    Output(DECLARATION_PERIOD_NAME_ID, "readonly"),
    Output(DECLARATION_PERIOD_START_DATE_ID, "date"),
    Output(DECLARATION_PERIOD_START_DATE_ID, "disabled"),
    Output(DECLARATION_PERIOD_END_DATE_ID, "date"),
    Output(DECLARATION_PERIOD_END_DATE_ID, "disabled"),
    Output(DECLARATION_PERIOD_VALIDATION_DATE_ID, "date"),
    Output(DECLARATION_PERIOD_VALIDATION_DATE_ID, "disabled"),
    Output(DECLARATION_PERIOD_PARAMS_ID, "style"),
    Output(DECLARATION_PERIODS_CREATE_CLICK_ID, "data"),
    Output(DECLARATION_PERIODS_SAVE_NEW_ID, "disabled"),
    Output(DECLARATION_PERIODS_STATUS_HIDDEN_ID, "data"),
    Input(DECLARATION_PERIODS_ID, "value"),
    Input(DECLARATION_PERIODS_CREATE_NEW_ID, "n_clicks"),
    State(DECLARATION_PERIODS_CREATE_CLICK_ID, "data"),
    State(DECLARATION_PERIODS_STATUS_HIDDEN_ID, "data"),
    State(DECLARATION_PERIODS_STATUS_VISIBLE_ID, "data"),
    prevent_initial_call=True,
)
def display_period_params(
    period_index: str,
    num_clicks: int,
    num_clicks_previous: int,
    status_hidden: int,
    status_visible: int,
) -> (str, bool, str, bool, str, bool, str, bool, str, int, int):
    """
    This callback displays the parameters of a selected period. It can be called either by selecting
    an existing period or creating a new one.
    """
    periods = get_declaration_periods(descending=False)

    # Hide the status alert after this callback (both variables must be equal)
    if status_hidden != status_visible:
        status_hidden = status_visible

    if num_clicks is not None and num_clicks != num_clicks_previous:
        today = datetime.now()
        if today.month < 7:
            start_month = 1
            end_month = 6
            end_day = 30
            semester = 1
        else:
            start_month = 7
            end_month = 12
            end_day = 31
            semester = 2
        period_name = f"{today.year}-S{semester}"
        start_date = datetime(today.year, start_month, 1)
        end_date = datetime(today.year, end_month, end_day, 23, 59)
        validation_date = datetime(today.year, end_month, 15)
        saved_clicks = num_clicks
        period_save_disabled = False

    else:
        try:
            period_index = int(period_index)
            if period_index < len(periods):
                period_name = periods[period_index].name
                start_date = periods[period_index].start_date
                end_date = periods[period_index].end_date
                validation_date = periods[period_index].validation_date
                saved_clicks = num_clicks_previous
                period_save_disabled = True
            else:
                raise Exception(
                    f"internal error: period_index has an invalid value ({period_index})"
                )
        except Exception as e:
            raise e

    return (
        period_name,
        True,
        start_date,
        True,
        end_date,
        True,
        validation_date,
        True,
        {"visibility": "visible"},
        saved_clicks,
        period_save_disabled,
        status_hidden,
    )


@app.callback(
    Output(DECLARATION_PERIODS_STATUS_ID, "children"),
    Output(DECLARATION_PERIODS_STATUS_ID, "color"),
    Output(DECLARATION_PERIODS_STATUS_VISIBLE_ID, "data"),
    Input(DECLARATION_PERIODS_SAVE_NEW_ID, "n_clicks"),
    State(DECLARATION_PERIOD_NAME_ID, "value"),
    State(DECLARATION_PERIOD_START_DATE_ID, "date"),
    State(DECLARATION_PERIOD_END_DATE_ID, "date"),
    State(DECLARATION_PERIOD_VALIDATION_DATE_ID, "date"),
    State(DECLARATION_PERIODS_STATUS_HIDDEN_ID, "data"),
    State(DECLARATION_PERIODS_STATUS_VISIBLE_ID, "data"),
    prevent_initial_call=True,
)
def save_new_period(
    n_clicks: int,
    name: str,
    start_date: str,
    end_date: str,
    validation_date: str,
    status_hidden: int,
    status_visible: int,
) -> (Any, str, int):
    """
    Save new period in database
    """
    from ositah.utils.hito_db import get_db
    from ositah.utils.hito_db_model import OSITAHValidationPeriod

    db = get_db()

    # Display the status alert after this callback (status_visible must be greater
    # than status_hidden)
    if status_visible <= status_hidden:
        status_visible = status_hidden + 1

    period = OSITAHValidationPeriod(
        name=name,
        start_date=start_date,
        end_date=end_date,
        validation_date=validation_date,
    )
    try:
        db.session.add(period)
        db.session.commit()
    except Exception as e:
        return (html.Div(repr(e)), "danger", status_visible)

    return (
        html.Div([f"Nouvelle période {name} ajoutée. ", html.A("Recharger", href="")]),
        "success",
        status_visible,
    )


@app.callback(
    Output(DECLARATION_PERIODS_STATUS_ID, "is_open"),
    Input(DECLARATION_PERIODS_STATUS_HIDDEN_ID, "data"),
    Input(DECLARATION_PERIODS_STATUS_VISIBLE_ID, "data"),
    prevent_initial_call=True,
)
def display_declaration_periods_status(status_hidden: int, status_visible: int) -> bool:
    """
    Callback to control whether the declaration periods status must be displayed or hidden.
    If status_visible > status_hidden, it must be displayed, else it must be hidden.
    """
    return status_visible > status_hidden

"""
Dash callbacks for Validation sub-application
"""

from datetime import datetime
from uuid import uuid4

import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import MATCH, Input, Output, State

from ositah.app import app
from ositah.apps.validation.parameters import *
from ositah.apps.validation.tables import (
    build_missing_agents_table,
    build_statistics_table,
    build_validation_table,
)
from ositah.apps.validation.tools import get_validation_data, project_declaration_snapshot
from ositah.utils.hito_db import get_db
from ositah.utils.menus import (
    TEAM_SELECTED_VALUE_ID,
    TEAM_SELECTION_DATE_ID,
    VALIDATION_PERIOD_SELECTED_ID,
    create_progress_bar,
)
from ositah.utils.period import get_validation_period_id


@app.callback(
    [
        Output(TAB_ID_DECLARATION_STATS, "children"),
        Output(TAB_ID_VALIDATION, "children"),
        Output(TAB_ID_MISSING_AGENTS, "children"),
        Output(VALIDATION_SAVED_INDICATOR_ID, "data"),
        Output(VALIDATION_SAVED_ACTIVE_TAB_ID, "data"),
    ],
    [
        Input(VALIDATION_LOAD_INDICATOR_ID, "data"),
        Input(VALIDATION_TAB_MENU_ID, "active_tab"),
        Input(TEAM_SELECTED_VALUE_ID, "data"),
        Input(VALIDATION_DECLARATIONS_SELECTED_ID, "data"),
    ],
    [
        State(TEAM_SELECTION_DATE_ID, "data"),
        State(VALIDATION_SAVED_INDICATOR_ID, "data"),
        State(VALIDATION_PERIOD_SELECTED_ID, "data"),
        State(VALIDATION_SAVED_ACTIVE_TAB_ID, "data"),
    ],
    prevent_initial_call=True,
)
def display_validation_tables(
    load_in_progress,
    active_tab: str,
    team: str,
    declaration_set: int,
    team_selection_date,
    previous_load_in_progress,
    period_date: str,
    previous_active_tab: str,
):
    """
    Display active tab contents after a team or an active tab change. Exact action depends on
    the value of the load in progress indicator. If it is equal to the previous value, it means
    this is the start of the update process: progress bar is displayed and a dcc.Interval is
    created to schedule again this callback after incrementing the load in progress indicator.
    This causes the callback to be reentered and this time it triggers the real processing for
    the tab resulting in the final update of the active tab contents. An empty content is
    returned for inactive tabs.

    :param load_in_progress: load in progress indicator
    :param tab: select tab name
    :param team: selected team
    :param declaration_set: selected declaration set (all, validated or non-validated ones)
    :param team_selection_date: last time the team selection was changed
    :param previous_load_in_progress: previous value of the load_in_progress indicator
    :param period_date: a date that must be inside the declaration period
    :param previous_active_tab: previously active tab
    :return: tab content (empty if the tab is not active)
    """

    tab_contents = []

    # Be sure to fill the return values in the same order as Output are declared
    tab_list = [TAB_ID_DECLARATION_STATS, TAB_ID_VALIDATION, TAB_ID_MISSING_AGENTS]
    for tab in tab_list:
        if team and len(team) > 0 and tab == active_tab:
            if load_in_progress > previous_load_in_progress and active_tab == previous_active_tab:
                if active_tab == TAB_ID_DECLARATION_STATS:
                    tab_contents.append(
                        build_statistics_table(team, team_selection_date, period_date)
                    )
                elif active_tab == TAB_ID_VALIDATION:
                    tab_contents.append(
                        build_validation_table(
                            team, team_selection_date, declaration_set, period_date
                        )
                    )
                elif active_tab == TAB_ID_MISSING_AGENTS:
                    tab_contents.append(
                        build_missing_agents_table(team, team_selection_date, period_date)
                    )
                else:
                    tab_contents.append(
                        dbc.Alert("Erreur interne: tab non supporté"), color="warning"
                    )
                previous_load_in_progress += 1
            else:
                component = html.Div(
                    [
                        create_progress_bar(team),
                        dcc.Interval(
                            id=VALIDATION_DISPLAY_INTERVAL_ID,
                            n_intervals=0,
                            max_intervals=1,
                            interval=500,
                        ),
                    ]
                )
                tab_contents.append(component)
        else:
            tab_contents.append("")

    tab_contents.extend([previous_load_in_progress, active_tab])

    return tab_contents


@app.callback(
    Output(VALIDATION_LOAD_INDICATOR_ID, "data"),
    Input(VALIDATION_DISPLAY_INTERVAL_ID, "n_intervals"),
    State(VALIDATION_SAVED_INDICATOR_ID, "data"),
    prevent_initial_call=True,
)
def display_validation_tables_trigger(n, previous_load_indicator):
    """
    Increment (change) of the input of display_validation_tables callback to get it fired a
    second time after displaying the progress bar. The output component must be updated each
    time the callback is entered to trigger the execution of the other callback, thus the
    choice of incrementing it at each call.

    :param n: n_interval property of the dcc.Interval (0 or 1)
    :return: 1 increment to previous value
    """

    return previous_load_indicator + 1


@app.callback(
    Output({"type": "validation-switch", "id": MATCH}, "value"),
    Input({"type": "validation-switch", "id": MATCH}, "value"),
    State({"type": "validation-agent-id", "id": MATCH}, "data"),
    State(TEAM_SELECTED_VALUE_ID, "data"),
    State(TEAM_SELECTION_DATE_ID, "data"),
    State(VALIDATION_PERIOD_SELECTED_ID, "data"),
    prevent_initial_call=True,
)
def validation_button_callback(value, agent_id, team, team_selection_date, period_date: str):
    """
    Function called as a callback for the validation button. It adds a validation entry for
    the selected agent with a timestamp allowing to get the validation history. Doesn't add an
    entry if the validation status is unchanged (should not happen).

    :param value: a list with of values with last one equals 1 if the switch is on, an empty
                  list or a list with 1 value (0) if the switch is off
    :param agent_id: the agent ID of the selected agent
    :param team: selected team
    :param team_selection_date: last time the team selection was changed
    :param period_date: a date that must be inside the declaration period
    :return: None
    """

    from ositah.utils.hito_db_model import OSITAHValidation

    db = get_db()
    session = db.session

    validation_data = get_validation_data(agent_id, period_date, session)

    # If the validation switch is on, add a new validation entry for the agent (except if there
    # is an existing validated entry but it should not happen) and save the associated project
    # declarations. If the switch is off and a validated entry exists, update the "validated"
    # attribute to false and do not add a new project declarations.
    switch_on = len(value) > 0 and value[len(value) - 1] > 0
    if switch_on:
        if validation_data is None or validation_data.validated != switch_on:
            validation_id = str(uuid4())
            validation_data = OSITAHValidation(
                id=validation_id,
                validated=switch_on,
                timestamp=datetime.now(),
                agent_id=agent_id,
                period_id=get_validation_period_id(period_date),
            )
            try:
                session.add(validation_data)
                # A flush() is required before calling project_declaration_snapshot() else the
                # first insert is lost
                # MJ 2023-07-12: hack to workaround a problem with flush() leading to an undefined
                # foreign key
                # session.flush()
                session.commit()
                project_declaration_snapshot(
                    agent_id,
                    validation_id,
                    team,
                    team_selection_date,
                    period_date,
                    session,
                )
                session.commit()
            except:  # noqa: E722
                session.rollback()
                raise

    elif validation_data.validated:
        validation_data.validated = switch_on
        # Keep track of the original timestamp
        validation_data.initial_timestamp = validation_data.timestamp
        validation_data.timestamp = datetime.now()
        session.commit()

    return value


@app.callback(
    Output(VALIDATION_DECLARATIONS_SELECTED_ID, "data"),
    Input(VALIDATION_DECLARATIONS_SWITCH_ID, "value"),
    prevent_initial_call=True,
)
def select_declarations_set(new_set):
    """
    This callback is used to forward to the validation table callback the selected declarations
    set through a dcc.Store that exists permanently in the page.

    :param new_set: selected declarations set
    :return: same value
    """

    return new_set

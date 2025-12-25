# Module containing helper functions to build/manage the menus and graphic objects

from datetime import datetime

import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import MATCH, Input, Output, State

from ositah.app import app
from ositah.utils.cache import clear_cached_data
from ositah.utils.exceptions import SessionDataMissing
from ositah.utils.period import get_declaration_periods, get_default_period_date
from ositah.utils.utils import GlobalParams, no_session_id_jumbotron

DATA_SELECTED_SOURCE_ID = "project-declaration-source"
DATA_SELECTION_SOURCE_ID = "project-declaration-source-button"

TEAM_SELECTED_VALUE_ID = "team-selected"
TEAM_SELECTION_MENU_ID = "team-selection-dropdown"
TEAM_SELECTION_DATE_ID = "team-selection-date"

VALIDATION_PERIOD_MENU_ID = "validation-period-dropdown"
VALIDATION_PERIOD_SELECTED_ID = "validation-period-selected"

# 'type' part of composite IDs
TABLE_TYPE_TABLE = "ositah-table"
TABLE_TYPE_DUMMY_STORE = "ositah-table-dummy-store"

LOAD_PROGRESS_BAR_ID = "validation-progress-bar"
LOAD_PROGRESS_BAR_INTERVAL_DURATION = 500  # Milliseconds
LOAD_PROGRESS_BAR_MAX_DURATION = 15  # Seconds

NEW_PAGE_INDICATOR_ID = "page-initial-load"


def team_list_dropdown(menu_id=TEAM_SELECTION_MENU_ID):
    """
    Build a dropdown menu from the teams associated with the current user session.

    :param menu_id: menu ID for the created dropdown menu
    :return: dcc.Dropdown object or a jumbotron in case of errors
    """

    global_params = GlobalParams()
    try:
        session_data = global_params.session_data
        if session_data.agent_teams and len(session_data.agent_teams) > 1:
            default_team = ""
        else:
            default_team = session_data.agent_teams[0]

    except SessionDataMissing:
        return no_session_id_jumbotron()

    periods = session_data.declaration_periods
    if periods is None:
        periods = get_declaration_periods()
        session_data.declaration_periods = periods
    default_period = get_default_period_date(
        periods, global_params.declaration_options["default_date"]
    )

    return dbc.Row(
        [
            dbc.Col(
                [
                    dbc.Label(html.B("Equipe")),
                    dcc.Dropdown(
                        id=menu_id,
                        options=[
                            {"label": team, "value": team} for team in session_data.agent_teams
                        ],
                        loading_state={"is_loading": True},
                        value=default_team,
                        placeholder="Sélectionner une équipe",
                    ),
                ],
                width=6,
                class_name="team_list_dropdown",
            ),
            dbc.Col(
                [
                    dbc.Label(html.B("Période")),
                    dcc.Dropdown(
                        id=VALIDATION_PERIOD_MENU_ID,
                        options=[
                            {
                                "label": period.label,
                                "value": period.start_date,
                            }
                            for period in periods
                        ],
                        value=default_period,
                        placeholder="Sélectionner une période",
                    ),
                ],
                width={"size": 4, "offset": 1},
                class_name="team_list_dropdown",
            ),
        ]
    )


def build_accordion(button_number, button_content, hidden_text, tooltip=None, class_list=""):
    """
    Function to build an accordion associated with the component passed in button_contents.

    :param button_number: the button number, must be unique for each button
    :param button_content: what will be put inside the button
    :param hidden_text: text to be displayed when the accordion is open
    :param tooltip: text to be displayed as an optional tooltip
    :param class_list: optional class list to add to the dbc.Card
    :return: the accordion element

    """

    return html.Div(
        [
            dbc.Accordion(
                dbc.AccordionItem(
                    hidden_text,
                    title=button_content,
                    class_name=class_list,
                ),
                id={"type": "accordion_toggle", "id": button_number},
                start_collapsed=True,
            ),
            dbc.Tooltip(
                tooltip,
                target={"type": "accordion_toggle", "id": button_number},
                placement="left",
                key=f"acccordion_tooltip_{button_number}",
            ),
        ]
    )


def create_progress_bar(
    team: str = None,
    duration: int = LOAD_PROGRESS_BAR_MAX_DURATION,
    interval: float = LOAD_PROGRESS_BAR_INTERVAL_DURATION,
):
    """
    Create a Div with a progress bar

    :param team: currently selected team
    :param duration: progress bar duration (seconds)
    :param interval: interval duration (millisecondes
    :return: Div
    """

    max_intervals = int(duration * 1000 / interval)

    return html.Div(
        [
            (
                html.Div(f"Chargement des données de l'équipe {team} en cours...")
                if team
                else html.Div()
            ),
            dcc.Interval(
                id="progress-interval",
                max_intervals=max_intervals,
                n_intervals=0,
                interval=LOAD_PROGRESS_BAR_INTERVAL_DURATION,
            ),
            dbc.Progress(id="progress", striped=True),
            dcc.Store(id="progress-bar-max-intervals", data=max_intervals),
        ],
        id=LOAD_PROGRESS_BAR_ID,
    )


@app.callback(
    [Output("progress", "value"), Output("progress", "label")],
    Input("progress-interval", "n_intervals"),
    State("progress-bar-max-intervals", "data"),
    prevent_initial_call=True,
)
def update_progress_bar(n, max_intervals):
    """
    Update the progress bar.

    :param n: number of intervals since the beginning
    :param max_intervals: maximum number of intervals (duration)
    :return:
    """

    progress = int(round(n * 100 / max_intervals))
    # only add text after 5% progress to ensure text isn't squashed too much
    return progress, f"{progress} %" if progress >= 5 else ""


@app.callback(
    Output({"type": "accordion_collapse", "id": MATCH}, "is_open"),
    Input({"type": "accordion_toggle", "id": MATCH}, "n_clicks"),
    State({"type": "accordion_collapse", "id": MATCH}, "is_open"),
    prevent_initial_call=True,
)
def toggle_agent_accordion(n_clicks, is_open) -> bool:
    """
    Callback function for the agent accordion.

    :param value: number of times the link was clicked
    :param is_open: whether the accordion is open or closed
    :return: List of n Output
    """

    if n_clicks:
        return not is_open


@app.callback(
    Output(TEAM_SELECTION_MENU_ID, "value"),
    Output(TEAM_SELECTED_VALUE_ID, "data"),
    Output(TEAM_SELECTION_DATE_ID, "data"),
    Output(VALIDATION_PERIOD_MENU_ID, "value"),
    Output(VALIDATION_PERIOD_SELECTED_ID, "data"),
    Output(TEAM_SELECTION_MENU_ID, "loading_state"),
    Input(TEAM_SELECTION_MENU_ID, "value"),
    Input(VALIDATION_PERIOD_MENU_ID, "value"),
    State(TEAM_SELECTED_VALUE_ID, "data"),
    State(DATA_SELECTED_SOURCE_ID, "children"),
    State(TEAM_SELECTION_DATE_ID, "data"),
    State(VALIDATION_PERIOD_SELECTED_ID, "data"),
    State(TEAM_SELECTION_MENU_ID, "loading_state"),
)
def save_team_and_period(
    selected_team,
    selected_period,
    previous_team,
    selected_source,
    team_selection_date,
    previous_period,
    loading_state,
):
    """
    Function to save the selected team and period in a dcc.Store. This will trigger other callbacks.
    Also clear the data cache. The value of the team selection dropdown is written back: it
    allows to update the initial value if one was saved into the dcc.Store.

    :param selected_team: team dropdown menu value
    :param selected_period: period dropdoan menu value
    :param previous_team: previously selected team
    :param selected_source: currently selected data source
    :param team_selection_date: date of the last team selection
    :param previous_period: previously selected period
    :param loading_state: loading state of the team selection menu
    :return: expected Output values
    """

    # Handle the initial display of the selection menu: if it was already displayed in another
    # page and a value was previously selected (saved in TEAM_SELECTED_VALUE_ID), use it as the
    # initial value (set it to this value through the callback). Do the same for the validation
    # period

    global_params = GlobalParams()
    try:
        session_data = global_params.session_data
    except SessionDataMissing:
        return no_session_id_jumbotron(), "", ""

    if "is_loading" in loading_state and loading_state["is_loading"]:
        team = previous_team
        # If previous_period is empty, means that it should be initialised with the pulldown
        # menu default value (in selected_period the first time the callback is executed)
        if previous_period == "":
            period = selected_period
        else:
            period = previous_period
    else:
        team = selected_team
        period = selected_period

    # Cache must be changed if the team has been changed or if the selected source doesn't match
    # the cached one
    if (
        team != previous_team
        or period != previous_period
        or session_data.project_declarations_source is None
        or selected_source != session_data.project_declarations_source
    ):
        clear_cached_data()
        selection_date = f"{datetime.now()}"
    else:
        selection_date = team_selection_date

    return team, team, selection_date, period, period, {"is_laoding": False}


# Client-side callback used to mark a table as sortable. To be marked sortable, a table must have
# an ID matching the ID type attribute TABLE_TYPE_TABLE and create a dcc.Store associated with
# an ID type attribute TABLE_TYPE_DUMMY_STORE
app.clientside_callback(
    """
    function make_table_sortable(dummy, table_id) {
        if (!(typeof table_id === 'string' || table_id instanceof String)) {
            table_id = JSON.stringify(table_id, Object.keys(table_id).sort());
        };
        /*alert('Mark sortable table with ID='+table_id);*/
        const tableObject = document.getElementById(table_id);
        sorttable.makeSortable(tableObject);
        return 0;
    }
    """,
    Output({"type": TABLE_TYPE_DUMMY_STORE, "id": MATCH}, "data"),
    Input({"type": TABLE_TYPE_TABLE, "id": MATCH}, "children"),
    State({"type": TABLE_TYPE_TABLE, "id": MATCH}, "id"),
    prevent_initial_call=True,
)


# Emulate former Jumbotron
def ositah_jumbotron(title: str, main_text: str, details: str = None, title_class: str = None):
    """
    Emulate Jumbotron component available in Bootstrap v4

    :param title: Jumbotron title
    :param main_text: main text
    :param details: optional additional text
    :return: html.div()
    """

    return html.Div(
        dbc.Container(
            [
                html.H1(title, className=f"display-3 {title_class if (title_class) else ''}"),
                html.P(
                    main_text,
                    className="lead",
                ),
                html.Hr(className="my-2"),
                html.P(details),
            ],
            fluid=True,
            className="py-3",
        ),
        className="p-3 bg-light rounded-3",
    )

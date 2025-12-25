# OSITAH sub-application to analyse data to NSIP
from typing import Dict

import dash
import dash_bootstrap_components as dbc
import numpy as np
import plotly.express as px
from dash import dcc, html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from ositah.app import app
from ositah.utils.cache import clear_cached_data
from ositah.utils.menus import (
    DATA_SELECTED_SOURCE_ID,
    DATA_SELECTION_SOURCE_ID,
    TABLE_TYPE_DUMMY_STORE,
    TABLE_TYPE_TABLE,
    TEAM_SELECTED_VALUE_ID,
    TEAM_SELECTION_DATE_ID,
    VALIDATION_PERIOD_SELECTED_ID,
    build_accordion,
    create_progress_bar,
    team_list_dropdown,
)
from ositah.utils.period import get_validation_period_dates
from ositah.utils.projects import (
    DATA_SOURCE_HITO,
    DATA_SOURCE_OSITAH,
    build_projects_data,
    get_team_projects,
)
from ositah.utils.utils import WEEK_HOURS, GlobalParams, general_error_jumbotron

ANALYSIS_TAB_MENU_ID = "report-tabs"
TAB_ID_ANALYSIS_GRAPHICS = "graphics-page"
TAB_ID_ANALYSIS_IJCLAB = "project-report-page"

TAB_MENU_ANALYSIS_GRAPHICS = "Graphiques"
TAB_MENU_ANALYSIS_IJCLAB = "Rapports"

TABLE_TEAM_PROJECTS_ID = "analysis-ijclab"

ANALYSIS_LOAD_INDICATOR_ID = "analysis-others-data-load-indicator"
ANALYSIS_SAVED_INDICATOR_ID = "analysis-others-saved-data-load-indicator"
ANALYSIS_TRIGGER_INTERVAL_ID = "analysis-others-display-callback-interval"
ANALYSIS_PROGRESS_BAR_MAX_DURATION = 8  # seconds
ANALYSIS_SAVED_ACTIVE_TAB_ID = "analysis-saved-active-tab"

GRAPHICS_DROPDOWN_ID = "graphics-type-selection"
GRAPHICS_DROPDOWN_MENU = "Types de graphique"
GRAPHICS_DM_CATEGORY_TIME_ID = "graphics-cateogry-time"
GRAPHICS_DM_CATEGORY_TIME_MENU = "Catégorie d'activités"
GRAPHICS_DM_LOCAL_PROJECTS_TIME_ID = "graphics-local-projects-time"
GRAPHICS_DM_LOCAL_PROJECTS_TIME_MENU = "Projets locaux"
GRAPHICS_DM_NSIP_PROJECTS_TIME_ID = "graphics-nsip-projects-time"
GRAPHICS_DM_NSIP_PROJECTS_TIME_MENU = "Projets NSIP"
GRAPHICS_DM_TEACHING_ACTIVITIES_TIME_ID = "graphics-teaching-activities-time"
GRAPHICS_DM_TEACHING_ACTIVITIES_TIME_MENU = "Enseignement"
GRAPHICS_DM_CONSULTANCY_ACTIVITIES_TIME_ID = "graphics-consultancy-activities-time"
GRAPHICS_DM_CONSULTANCY_ACTIVITIES_TIME_MENU = "Consultance & Expertise"
GRAPHICS_DM_SUPPORT_ACTIVITIES_TIME_ID = "graphics-support-activities-time"
GRAPHICS_DM_SUPPORT_ACTIVITIES_TIME_MENU = "Service & Support"
GRAPHICS_AREA_DIV_ID = "graphics-area"


def define_exported_column_names() -> Dict[str, str]:
    """
    Function to build the EXPORT_COLUMN_NAMES dict from colum names defined in global parameters

    :return: dict
    """

    global_params = GlobalParams()
    columns = global_params.columns

    return {
        columns["category"]: "Type d'activité",
        columns["fullname"]: "Agent",
        columns["hours"]: "Nombre d'heures",
        columns["masterproject"]: "Masterprojet",
        columns["team"]: "Equipe",
        columns["project"]: "Projet",
    }


# Maps column names from queries to displayed column names in table/CSV
EXPORT_COLUMN_NAMES = define_exported_column_names()


def ijclab_team_export_table(team, team_selection_date, period_date: str, source):
    """
    Build the project list contributed by the selected team and the related time declarations and
    return a table.

    :param team: selected team
    :param team_selection_date: last time the team selection was changed
    :param period_date: a date that must be inside the declaration period
    :param source: whether to use Hito (non validated) or OSITAH (validated) as a data source
    :return: dbc.Table
    """

    if team is None:
        return html.Div("")

    global_params = GlobalParams()
    columns = global_params.columns

    start_date, end_date = get_validation_period_dates(period_date)

    projects_data, declaration_list = build_projects_data(
        team, team_selection_date, period_date, source
    )
    if projects_data is None or declaration_list is None:
        if source == DATA_SOURCE_HITO:
            msg = f"L'équipe '{team}' ne contribue à aucun projet"
        else:
            msg = f"Aucune données validées n'existe pour l'équipe '{team}'"
        msg += (
            f" pour la période du {start_date.strftime('%Y-%m-%d')} au"
            f" {end_date.strftime('%Y-%m-%d')}"
        )
        return html.Div([dbc.Alert(msg, color="warning"), add_source_selection_switch(source)])

    table_columns = [columns["masterproject"], columns["project"], columns["hours"]]

    table_header = [
        html.Thead(
            html.Tr(
                [
                    *[
                        html.Th(
                            [
                                html.I(f"{EXPORT_COLUMN_NAMES[c]} "),
                                html.I(className="fas fa-sort mr-3"),
                            ],
                            className="text-center",
                        )
                        for c in table_columns
                    ],
                ]
            )
        )
    ]

    table_body = [
        html.Tbody(
            [
                html.Tr(
                    [
                        html.Td(
                            projects_data.iloc[i - 1][columns["masterproject"]],
                            className="align-middle",
                            key=f"analysis-table-cell-{i}-masterproject",
                        ),
                        html.Td(
                            projects_data.iloc[i - 1][columns["project"]],
                            className="align-middle",
                            key=f"analysis-table-cell-{i}-project",
                        ),
                        html.Td(
                            build_accordion(
                                i,
                                projects_data.iloc[i - 1][columns["hours"]],
                                project_agents_time(
                                    declaration_list,
                                    projects_data.iloc[i - 1][columns["activity"]],
                                ),
                                f"{projects_data.iloc[i-1][columns['weeks']]} semaines",
                            ),
                            className="accordion",
                            key=f"analysis-table-cell-{i}-time",
                        ),
                    ]
                )
                for i in range(1, len(projects_data) + 1)
            ]
        )
    ]

    if source == DATA_SOURCE_OSITAH:
        page_title = f"Contributions par projet validées de '{team}'"
    else:
        page_title = f"Contributions par projet déclarées (non validées) de '{team}'"
    page_title += f" du {start_date.strftime('%Y-%m-%d')} au {end_date.strftime('%Y-%m-%d')}"

    return html.Div(
        [
            html.Div(
                [
                    dbc.Row(
                        [
                            dbc.Col(dbc.Alert(page_title), width=8),
                            dbc.Col(
                                [
                                    dbc.Button("Export CSV", id="ijclab-export-file-button"),
                                    dcc.Download(id="ijclab-export-file-download"),
                                ],
                                width={"size": 2, "offset": 2},
                            ),
                        ]
                    ),
                    add_source_selection_switch(source),
                ]
            ),
            html.P(""),
            dbc.Table(
                table_header + table_body,
                id={"type": TABLE_TYPE_TABLE, "id": TABLE_TEAM_PROJECTS_ID},
                bordered=True,
                hover=True,
                striped=True,
                class_name="sortable",
            ),
        ]
    )


def ijclab_graphics(team, team_selection_date, period_date: str, source):
    """
    Build various graphics from declarations. This function just creates the basic structure of
    the graphic page and read the data. The actual graphic will be displayed by the callback
    associated with the dropdown menu used to select the graphics type.

    :param team: selected team
    :param team_selection_date: last time the team selection was changed
    :param period_date: a date that must be inside the declaration period
    :param source: whether to use Hito (non validated) or OSITAH (validated) as a data source
    :return: graphics and associated menus
    """

    if team is None:
        return html.Div("")

    start_date, end_date = get_validation_period_dates(period_date)

    projects_data, declaration_list = build_projects_data(
        team, team_selection_date, period_date, source
    )
    if projects_data is None or declaration_list is None:
        if source == DATA_SOURCE_HITO:
            msg = f"L'équipe '{team}' ne contribue à aucun projet"
        else:
            msg = f"Aucune données validées n'existe pour l'équipe '{team}'"
        msg += (
            f" pour la période du {start_date.strftime('%Y-%m-%d')} au"
            f" {end_date.strftime('%Y-%m-%d')}"
        )
        return html.Div([dbc.Alert(msg, color="warning"), add_source_selection_switch(source)])

    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(add_source_selection_switch(source), width=8),
                    dbc.Col(graphics_dropdown_menu(), width={"size": 3, "offset": 1}),
                ]
            ),
            html.Div(id=GRAPHICS_AREA_DIV_ID),
        ]
    )


def add_source_selection_switch(current_source):
    """
    Add a dbc.RadioItems to select the data source.

    :param current_source: currently selected source
    :return: dbc.RadioItems
    """

    return dbc.Row(
        [
            dbc.RadioItems(
                options=[
                    {"label": "Toutes les déclarations", "value": DATA_SOURCE_HITO},
                    {
                        "label": "Déclarations validées uniquement",
                        "value": DATA_SOURCE_OSITAH,
                    },
                ],
                value=current_source,
                id=DATA_SELECTION_SOURCE_ID,
                inline=True,
            ),
        ],
        justify="center",
    )


def project_agents_time(declarations, project):
    """
    Return a HTML Div with the list of agents who contributed to the project and their
    declared time.

    :param declarations: dataframe with the contribution of each agent to each project
    :param project: project fullname
    :return:
    """

    global_params = GlobalParams()
    columns = global_params.columns

    project_agents = declarations[declarations[columns["activity"]] == project]
    project_agents.loc[:, columns["hours"]] = np.round(project_agents[columns["hours"]]).astype(
        "int"
    )
    project_agents.loc[:, columns["weeks"]] = np.round(
        project_agents.loc[:, columns["hours"]] / WEEK_HOURS, 1
    )
    if global_params.analysis_params["contributions_sorted_by_name"]:
        sort_by = ["nom", columns["hours"]]
        sort_ascending = True
    else:
        sort_by = [columns["hours"], "nom"]
        sort_ascending = False
    project_agents.sort_values(
        by=sort_by, ascending=sort_ascending, ignore_index=True, inplace=True
    )
    return html.Div(
        [
            html.Div(
                (
                    f"{project_agents.iloc[i]['fullname']}:"
                    f" {project_agents.iloc[i][columns['hours']]}"
                    f" ({project_agents.iloc[i][columns['weeks']]} sem.)"
                )
            )
            for i in range(len(project_agents))
        ]
    )


def graphics_dropdown_menu():
    """
    Build the dropdown menu to select the graphics type

    :return: dropdown menu
    """

    return dbc.DropdownMenu(
        [
            dbc.DropdownMenuItem(
                GRAPHICS_DM_CATEGORY_TIME_MENU,
                id=GRAPHICS_DM_CATEGORY_TIME_ID,
                n_clicks=0,
            ),
            dbc.DropdownMenuItem(divider=True),
            dbc.DropdownMenuItem(
                GRAPHICS_DM_NSIP_PROJECTS_TIME_MENU,
                id=GRAPHICS_DM_NSIP_PROJECTS_TIME_ID,
                n_clicks=0,
            ),
            dbc.DropdownMenuItem(
                GRAPHICS_DM_LOCAL_PROJECTS_TIME_MENU,
                id=GRAPHICS_DM_LOCAL_PROJECTS_TIME_ID,
                n_clicks=0,
            ),
            dbc.DropdownMenuItem(divider=True),
            dbc.DropdownMenuItem(
                GRAPHICS_DM_TEACHING_ACTIVITIES_TIME_MENU,
                id=GRAPHICS_DM_TEACHING_ACTIVITIES_TIME_ID,
                n_clicks=0,
            ),
            dbc.DropdownMenuItem(
                GRAPHICS_DM_CONSULTANCY_ACTIVITIES_TIME_MENU,
                id=GRAPHICS_DM_CONSULTANCY_ACTIVITIES_TIME_ID,
                n_clicks=0,
            ),
            dbc.DropdownMenuItem(
                GRAPHICS_DM_SUPPORT_ACTIVITIES_TIME_MENU,
                id=GRAPHICS_DM_SUPPORT_ACTIVITIES_TIME_ID,
                n_clicks=0,
            ),
        ],
        id=GRAPHICS_DROPDOWN_ID,
        label=GRAPHICS_DROPDOWN_MENU,
    )


def analysis_submenus():
    """
    Build the tabs menus of the export subapplication

    :return: DBC Tabs
    """

    return dbc.Tabs(
        [
            dbc.Tab(
                id=TAB_ID_ANALYSIS_IJCLAB,
                tab_id=TAB_ID_ANALYSIS_IJCLAB,
                label=TAB_MENU_ANALYSIS_IJCLAB,
            ),
            dbc.Tab(
                id=TAB_ID_ANALYSIS_GRAPHICS,
                tab_id=TAB_ID_ANALYSIS_GRAPHICS,
                label=TAB_MENU_ANALYSIS_GRAPHICS,
            ),
        ],
        id=ANALYSIS_TAB_MENU_ID,
    )


def analysis_layout():
    """
    Build the layout for this application, after reading the data if necessary.

    :return: application layout
    """

    return html.Div(
        [
            html.H1("Analyse des déclarations"),
            team_list_dropdown(),
            # The following dcc.Store is used to ensure that the the ijclab_export input exists
            # before the export page is created
            dcc.Store(id=DATA_SELECTED_SOURCE_ID, data=DATA_SOURCE_HITO),
            html.Div(analysis_submenus(), id="analysis-submenus", style={"marginTop": "3em"}),
            dcc.Store(id=ANALYSIS_LOAD_INDICATOR_ID, data=0),
            dcc.Store(id=ANALYSIS_SAVED_INDICATOR_ID, data=0),
            dcc.Store(id=ANALYSIS_SAVED_ACTIVE_TAB_ID, data=""),
            dcc.Store(
                id={"type": TABLE_TYPE_DUMMY_STORE, "id": TABLE_TEAM_PROJECTS_ID},
                data=0,
            ),
        ]
    )


@app.callback(
    Output(DATA_SELECTED_SOURCE_ID, "data"),
    Input(DATA_SELECTION_SOURCE_ID, "value"),
    State(DATA_SELECTED_SOURCE_ID, "data"),
    prevent_initial_call=True,
)
def select_data_source(new_source, previous_source):
    """
    This callback is used to forward to the export callback the selected source through a
    dcc.Store that exists before the page is created. It also clears the data cache if
    the source has been changed.

    :param new_source: value to forward to the dcc.Store
    :param previous_source: previous value of the selection
    :return: new_source value
    """

    if new_source != previous_source:
        clear_cached_data()

    return new_source


@app.callback(
    [
        Output(TAB_ID_ANALYSIS_IJCLAB, "children"),
        Output(TAB_ID_ANALYSIS_GRAPHICS, "children"),
        Output(ANALYSIS_SAVED_INDICATOR_ID, "data"),
        Output(ANALYSIS_SAVED_ACTIVE_TAB_ID, "data"),
    ],
    [
        Input(ANALYSIS_LOAD_INDICATOR_ID, "data"),
        Input(ANALYSIS_TAB_MENU_ID, "active_tab"),
        Input(TEAM_SELECTED_VALUE_ID, "data"),
        Input(DATA_SELECTED_SOURCE_ID, "data"),
    ],
    [
        State(TEAM_SELECTION_DATE_ID, "data"),
        State(ANALYSIS_SAVED_INDICATOR_ID, "data"),
        State(VALIDATION_PERIOD_SELECTED_ID, "data"),
        State(ANALYSIS_SAVED_ACTIVE_TAB_ID, "data"),
    ],
    prevent_initial_call=True,
)
def display_analysis_tables(
    load_in_progress,
    active_tab,
    team,
    data_source,
    team_selection_date,
    previous_load_in_progress,
    period_date: str,
    previous_active_tab,
):
    """
    Display active tab contents after a team or an active tab change. Exact action depends on the
    value of the load in progress indicator. If it is equal to the previous value, it means this
    is the start of the update process: progress bar is displayed and a dcc.Interval is created
    to schedule again this callback after incrementing the load in progress indicator. This causes
    the callback to be reentered and this time it triggers the real processing for the tab
    resulting in the final update of the active tab contents. An empty content is returned for
    inactive tabs.

    :param load_in_progress: load in progress indicator
    :param tab: tab name
    :param team: selected team
    :param data_source: Hito (non-validated declarations) or OSITAH (validated declarations)
    :param team_selection_date: last time the team selection was changed
    :param previous_load_in_progress: previous value of the load_in_progress indicator
    :param period_date: a date that must be inside the declaration period
    :param previous_active_tab: previously active tab
    :return: tab content
    """

    tab_contents = []

    # Be sure to fill the return values in the same order as Output are declared
    tab_list = [TAB_ID_ANALYSIS_IJCLAB, TAB_ID_ANALYSIS_GRAPHICS]
    for tab in tab_list:
        if team and len(team) > 0 and tab == active_tab:
            if load_in_progress > previous_load_in_progress and active_tab == previous_active_tab:
                if tab == TAB_ID_ANALYSIS_IJCLAB:
                    tab_contents.append(
                        ijclab_team_export_table(
                            team, team_selection_date, period_date, data_source
                        )
                    )
                elif tab == TAB_ID_ANALYSIS_GRAPHICS:
                    tab_contents.append(
                        ijclab_graphics(team, team_selection_date, period_date, data_source)
                    )
                else:
                    tab_contents.append(
                        dbc.Alert("Erreur interne: tab non supporté"), color="warning"
                    )
                previous_load_in_progress += 1
            else:
                component = html.Div(
                    [
                        create_progress_bar(team, duration=ANALYSIS_PROGRESS_BAR_MAX_DURATION),
                        dcc.Interval(
                            id=ANALYSIS_TRIGGER_INTERVAL_ID,
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
    Output(ANALYSIS_LOAD_INDICATOR_ID, "data"),
    Input(ANALYSIS_TRIGGER_INTERVAL_ID, "n_intervals"),
    State(ANALYSIS_SAVED_INDICATOR_ID, "data"),
    prevent_initial_call=True,
)
def display_tables_trigger(n, previous_load_indicator):
    """
    Increment (change) of the input of display_tables_trigger callback to get it fired a
    second time after displaying the progress bar. The output component must be updated each
    time the callback is entered to trigger the execution of the other callback, thus the
    choice of incrementing it at each call.

    :param n: n_interval property of the dcc.Interval (0 or 1)
    :return: 1 increment to previous value
    """

    return previous_load_indicator + 1


@app.callback(
    Output("ijclab-export-file-download", "data"),
    Input("ijclab-export-file-button", "n_clicks"),
    [
        State(TEAM_SELECTED_VALUE_ID, "data"),
        State(TEAM_SELECTION_DATE_ID, "data"),
        State(DATA_SELECTED_SOURCE_ID, "data"),
        State(VALIDATION_PERIOD_SELECTED_ID, "data"),
    ],
    prevent_initial_call=True,
)
def ijclab_export_to_csv(_, team, team_selection_date, source, period_date):
    """
    Generate a CSV file for the selected team, using the appropriate data source.

    :param _: unused, just an input to trigger the callback
    :param team: selected team
    :param team_selection_date: timestamp of the last change in team selection
    :param period_date: a date that must be inside the declaration period
    :return: None
    """

    global_params = GlobalParams()
    columns = global_params.columns

    declaration_list = get_team_projects(team, team_selection_date, period_date, source)
    if declaration_list is None:
        return dbc.Alert(
            f"L'équipe '{team}' ne contribue à aucun projet actuellement",
            color="warning",
        )

    exported_data = declaration_list[
        [
            columns["masterproject"],
            columns["project"],
            columns["category"],
            columns["fullname"],
            columns["team"],
            columns["hours"],
        ]
    ]
    exported_data.loc[:, columns["hours"]] = np.round(exported_data[columns["hours"]]).astype("int")
    column_renames = {}
    for c in exported_data.columns.tolist():
        if c in EXPORT_COLUMN_NAMES:
            column_renames[c] = EXPORT_COLUMN_NAMES[c]
    if len(column_renames.keys()) > 0:
        exported_data.rename(columns=column_renames, inplace=True)

    return dict(
        content=exported_data.to_csv(index=False, sep=";"),
        filename="project_contributions.csv",
    )


@app.callback(
    Output(GRAPHICS_AREA_DIV_ID, "children"),
    Output(GRAPHICS_DROPDOWN_ID, "label"),
    Output(GRAPHICS_AREA_DIV_ID, "style"),
    Input(GRAPHICS_DM_CATEGORY_TIME_ID, "n_clicks"),
    Input(GRAPHICS_DM_NSIP_PROJECTS_TIME_ID, "n_clicks"),
    Input(GRAPHICS_DM_LOCAL_PROJECTS_TIME_ID, "n_clicks"),
    Input(GRAPHICS_DM_TEACHING_ACTIVITIES_TIME_ID, "n_clicks"),
    Input(GRAPHICS_DM_CONSULTANCY_ACTIVITIES_TIME_ID, "n_clicks"),
    Input(GRAPHICS_DM_SUPPORT_ACTIVITIES_TIME_ID, "n_clicks"),
    State(TEAM_SELECTED_VALUE_ID, "data"),
    State(TEAM_SELECTION_DATE_ID, "data"),
    State(VALIDATION_PERIOD_SELECTED_ID, "data"),
    State(DATA_SELECTED_SOURCE_ID, "data"),
    State(GRAPHICS_DROPDOWN_ID, "label"),
    prevent_initial_call=True,
)
def display_graphics(
    _1,
    _2,
    _3,
    _4,
    _5,
    _6,
    team,
    team_selection_date,
    period_date,
    data_source,
    dropdown_label,
):
    """
    Display the selected graphics type

    :param _n: n_clicks property for each menu item used as input
    :param team: selected team
    :param team_selection_date: last time the team selection was changed
    :param period_date: a date that must be inside the declaration period
    :param data_source: Hito (non-validated declarations) or OSITAH (validated declarations)
    :param dropdown_label: Dropdown menu label
    :return: dcc.Graph
    """

    global_params = GlobalParams()
    columns = global_params.columns

    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    else:
        selected_item = ctx.triggered[0]["prop_id"].split(".")[0]

    projects_data, _ = build_projects_data(team, team_selection_date, period_date, data_source)

    if selected_item in [
        GRAPHICS_DM_NSIP_PROJECTS_TIME_ID,
        GRAPHICS_DM_LOCAL_PROJECTS_TIME_ID,
        GRAPHICS_DM_SUPPORT_ACTIVITIES_TIME_ID,
    ]:
        if selected_item == GRAPHICS_DM_NSIP_PROJECTS_TIME_ID:
            activity_data = projects_data.loc[projects_data[columns["category"]] == "nsip_project"]
            fig_title = "Temps par masterprojet et projet NSIP"
            y_column = columns["masterproject"]
            new_dropdown_label = GRAPHICS_DM_NSIP_PROJECTS_TIME_MENU
        elif selected_item == GRAPHICS_DM_LOCAL_PROJECTS_TIME_ID:
            activity_data = projects_data.loc[projects_data[columns["category"]] == "local_project"]
            fig_title = "Temps par projet local"
            y_column = "project_short"
            new_dropdown_label = GRAPHICS_DM_LOCAL_PROJECTS_TIME_MENU
        elif selected_item == GRAPHICS_DM_SUPPORT_ACTIVITIES_TIME_ID:
            activity_data = projects_data.loc[projects_data[columns["category"]] == "service"]
            fig_title = "Activités de Service & Support"
            y_column = "project_short"
            new_dropdown_label = GRAPHICS_DM_SUPPORT_ACTIVITIES_TIME_MENU
        else:
            return general_error_jumbotron(
                f"Erreur interne : '{selected_item}' non supporté pour un graphique en barre"
            )

        bar_num = len(activity_data[columns["project"]].unique())
        fig_height = "calc(100vh - 300px)"

        if activity_data.empty:
            fig = None
            fig_area_style = None
        else:
            fig = px.bar(
                activity_data,
                x=columns["hours"],
                y=y_column,
                color=columns["project"],
                orientation="h",
                height=200 + (30 * bar_num),
                title=fig_title,
            )
            fig.update_layout(
                showlegend=False,
                yaxis={"categoryorder": "category descending"},
            )
            fig_area_style = {
                "max-height": fig_height,
                "overflow-y": "scroll",
                "position": "relative",
            }

    elif selected_item in [
        GRAPHICS_DM_CATEGORY_TIME_ID,
        GRAPHICS_DM_TEACHING_ACTIVITIES_TIME_ID,
        GRAPHICS_DM_CONSULTANCY_ACTIVITIES_TIME_ID,
    ]:
        if selected_item == GRAPHICS_DM_CATEGORY_TIME_ID:
            activity_data = projects_data
            fig_title = "Temps par catégorie d'activités"
            y_column = columns["category"]
            new_dropdown_label = GRAPHICS_DM_CATEGORY_TIME_MENU
        elif selected_item == GRAPHICS_DM_TEACHING_ACTIVITIES_TIME_ID:
            activity_data = projects_data.loc[projects_data[columns["category"]] == "enseignement"]
            fig_title = "Activités d'enseignement"
            y_column = columns["project"]
            new_dropdown_label = GRAPHICS_DM_TEACHING_ACTIVITIES_TIME_MENU
        elif selected_item == GRAPHICS_DM_CONSULTANCY_ACTIVITIES_TIME_ID:
            activity_data = projects_data.loc[projects_data[columns["category"]] == "consultance"]
            fig_title = "Activités de Consultance et Expertise"
            y_column = columns["project"]
            new_dropdown_label = GRAPHICS_DM_CONSULTANCY_ACTIVITIES_TIME_MENU
        else:
            return general_error_jumbotron(
                f"Erreur interne : '{selected_item}' non supporté pour un graphique en barre"
            )

        fig_area_style = None
        fig_height = 400

        if activity_data.empty:
            fig = None
        else:
            fig = px.pie(
                activity_data,
                values=columns["hours"],
                names=y_column,
                title=fig_title,
                height=fig_height,
            )

    else:
        return (
            general_error_jumbotron(f"Graphics type '{selected_item}' not yet implemented"),
            dropdown_label,
            None,
        )

    if fig is None:
        return (
            dbc.Alert(f"Aucune activité correspondant à {new_dropdown_label}", color="warning"),
            dropdown_label,
            fig_area_style,
        )
    else:
        return (
            dcc.Graph("graphics-figure", figure=fig),
            new_dropdown_label,
            fig_area_style,
        )

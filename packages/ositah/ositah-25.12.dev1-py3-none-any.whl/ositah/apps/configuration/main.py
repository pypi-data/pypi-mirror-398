"""
OSITAH subapplication to manage the configuration

This file contains only the layout definitions
"""

from datetime import date

from dash import dcc

from ositah.apps.configuration.callbacks import *
from ositah.utils.menus import TABLE_TYPE_DUMMY_STORE
from ositah.utils.projects import MASTERPROJECT_DELETED_ACTIVITY
from ositah.utils.utils import AUTHORIZED_ROLES, HITO_ROLE_PROJECT_MGR


def configuration_layout():
    """
    Build the layout for this application, after reading the data if necessary.

    :return: application layout
    """

    return html.Div(
        [
            html.H1("Configuration OSITAH"),
            html.Div(
                configuration_submenus(),
                id="configuration-submenus",
                style={"marginTop": "3em"},
            ),
            # The following dcc.Store coupled with tables must be created in the layout for
            # the callback to work
            dcc.Store(
                id={"type": TABLE_TYPE_DUMMY_STORE, "id": TABLE_NSIP_PROJECT_SYNC_ID},
                data=0,
            ),
        ]
    )


def declaration_periods_layout():
    """
    Define the layout specific to the management of declaration periods

    :return: html.Div component
    """

    declaration_periods = get_declaration_periods(descending=False)
    declaration_period_items = []
    i = 0
    for period in declaration_periods:
        declaration_period_items.append({"label": period.name, "value": i})
        i += 1

    # Disable creation of a new (next) period if the period matching the current already exists
    today = date.today().isoformat()
    if (
        len(declaration_periods) > 0
        and today >= declaration_periods[-1].start_date
        and today <= declaration_periods[-1].end_date
    ):
        current_period_exists = True
    else:
        current_period_exists = False

    period_params = [
        dbc.Row(
            [
                dbc.Label(
                    "Date de début",
                    html_for=DECLARATION_PERIOD_START_DATE_ID,
                    style={"fontWeight": "bold"},
                    width="5",
                ),
                dbc.Col(
                    dcc.DatePickerSingle(
                        id=DECLARATION_PERIOD_START_DATE_ID,
                        month_format="MMMM Y",
                        placeholder="MMMM Y",
                    ),
                    width="auto",
                    class_name="me-3",
                ),
            ],
            style={"marginBottom": "10px"},
        ),
        dbc.Row(
            [
                dbc.Label(
                    "Date de validation",
                    html_for=DECLARATION_PERIOD_VALIDATION_DATE_ID,
                    style={"fontWeight": "bold"},
                    width="5",
                ),
                dbc.Col(
                    dcc.DatePickerSingle(
                        id=DECLARATION_PERIOD_VALIDATION_DATE_ID,
                        month_format="MMMM Y",
                        placeholder="MMMM Y",
                    ),
                    width="auto",
                    class_name="me-3",
                ),
            ],
            style={"marginBottom": "10px"},
        ),
        dbc.Row(
            [
                dbc.Label(
                    "Date de fin",
                    html_for=DECLARATION_PERIOD_END_DATE_ID,
                    style={"fontWeight": "bold"},
                    width="5",
                ),
                dbc.Col(
                    dcc.DatePickerSingle(
                        id=DECLARATION_PERIOD_END_DATE_ID,
                        month_format="MMMM Y",
                        placeholder="MMMM Y",
                    ),
                    width="auto",
                    class_name="me-3",
                ),
            ],
            style={"marginBottom": "10px"},
        ),
        dbc.Row(
            [
                dbc.Label(
                    "Nom",
                    html_for=DECLARATION_PERIOD_NAME_ID,
                    style={"fontWeight": "bold"},
                    width="5",
                ),
                dbc.Col(
                    dbc.Input(
                        type="start_date",
                        id=DECLARATION_PERIOD_NAME_ID,
                        placeholder="Nom de la période",
                    ),
                    width="6",
                    class_name="me-3",
                ),
            ],
        ),
    ]

    return html.Div(
        [
            html.P(),
            dbc.Alert(id=DECLARATION_PERIODS_STATUS_ID, is_open=False),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Label(html.B("Périodes")),
                            dbc.Select(
                                id=DECLARATION_PERIODS_ID,
                                options=declaration_period_items,
                                html_size=DECLARATION_PERIODS_LIST_MAX_SIZE,
                            ),
                        ],
                        width={"offset": 1, "size": 3},
                    ),
                    dbc.Col(
                        dbc.Form(period_params),
                        id=DECLARATION_PERIOD_PARAMS_ID,
                        style={
                            "border": "1px solid",
                            "borderRadius": "4px",
                            "borderSizing": "border-box",
                            "padding": "10px 10px",
                            "visibility": "hidden",
                        },
                        width={"offset": 1, "size": 4},
                    ),
                ],
                align="center",
                justify="start",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            dbc.Button(
                                "Nouveau semestre",
                                id=DECLARATION_PERIODS_CREATE_NEW_ID,
                                disabled=current_period_exists,
                            ),
                            id=DECLARATION_PERIODS_CREATE_DIV_ID,
                        ),
                        width={"size": 3, "offset": 0},
                    ),
                    dbc.Col(
                        dbc.Button(
                            "Valider",
                            id=DECLARATION_PERIODS_SAVE_NEW_ID,
                            disabled=True,
                        ),
                        width={"size": 3, "offset": 0},
                    ),
                    dbc.Tooltip(
                        (
                            "Le semestre courant existe déjà"
                            if current_period_exists
                            else "Ajoute le semestre courant"
                        ),
                        target=DECLARATION_PERIODS_CREATE_DIV_ID,
                        placement="bottom",
                    ),
                ],
                justify="evenly",
                style={"marginTop": "3em"},
            ),
            dcc.Store(id=DECLARATION_PERIODS_CREATE_CLICK_ID, data=0),
            # The 2 following Stores are used to control if the status must be displayed or not.
            # If DECLARATION_PERIODS_STATUS_VISIBLE_ID > DECLARATION_PERIODS_STATUS_HIDDEN_ID,
            # it must be displayed else it must be hidden.
            dcc.Store(id=DECLARATION_PERIODS_STATUS_HIDDEN_ID, data=-0),
            dcc.Store(id=DECLARATION_PERIODS_STATUS_VISIBLE_ID, data=0),
        ]
    )


def nsip_sync_layout():
    """
    Define the layout specific to the NSIP project synchronisation

    :return: html.Div component
    """

    return html.Div(
        [
            html.P(),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.RadioItems(
                            id=NSIP_SYNC_ACTIVITY_TYPE_ID,
                            options=[
                                {
                                    "label": "Projets",
                                    "value": NSIP_SYNC_ACTIVITY_TYPE_PROJECT,
                                },
                                {
                                    "label": "Autres activités",
                                    "value": NSIP_SYNC_ACTIVITY_TYPE_OTHER,
                                },
                            ],
                            value=NSIP_SYNC_ACTIVITY_TYPE_PROJECT,
                        ),
                        width={"offset": 1, "size": 2},
                    ),
                    dbc.Col(
                        dbc.Button(
                            "Differences OSITAH/NSIP",
                            id=NSIP_SYNC_SHOW_DIFF_ID,
                            color="secondary",
                            className="me-1",
                        ),
                        width={"offset": 1, "size": 3},
                    ),
                    dbc.Col(
                        dbc.Button(
                            "Mise à jour OSITAH",
                            id=NSIP_SYNC_APPLY_DIFF_ID,
                            color="secondary",
                            className="me-1",
                            disabled=True,
                        ),
                        width={"offset": 1, "size": 2},
                    ),
                ]
            ),
            html.P(),
            html.Div(id=NSIP_SYNC_CONTENT_ID),
        ]
    )


def project_teams_layout():
    """
    Define the layout specific to the configuration of project teams

    :return: html.Div component
    """

    activities = get_all_hito_activities(True)
    masterproject_items = []
    for masterproject in sorted(activities.masterproject.unique(), key=lambda x: x.upper()):
        if masterproject != MASTERPROJECT_DELETED_ACTIVITY:
            masterproject_items.append({"label": masterproject, "value": masterproject})

    return html.Div(
        [
            html.P(),
            dbc.Alert(id=ACTIVITY_TEAMS_STATUS_ID, is_open=False),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Label(html.B("Masterprojet")),
                            dbc.Select(
                                id=ACTIVITY_TEAMS_MASTERPROJECTS_ID,
                                options=masterproject_items,
                                html_size=ACTIVITY_TEAMS_LIST_MAX_SIZE,
                            ),
                        ],
                        width={"size": ACTIVITY_TEAMS_LIST_BOX_WIDTH, "offset": 0},
                        xxl={"size": ACTIVITY_TEAMS_LIST_BOX_WIDTH_XXL, "offset": 0},
                    ),
                    dbc.Col(
                        [
                            dbc.Label(html.B("Projet")),
                            dbc.Select(
                                id=ACTIVITY_TEAMS_PROJECTS_ID,
                                html_size=ACTIVITY_TEAMS_LIST_MAX_SIZE,
                            ),
                        ],
                        width={
                            "size": ACTIVITY_TEAMS_LIST_BOX_WIDTH,
                            "offset": ACTIVITY_TEAMS_LIST_BOX_INTERVAL,
                        },
                        xxl={
                            "size": ACTIVITY_TEAMS_LIST_BOX_WIDTH_XXL,
                            "offset": ACTIVITY_TEAMS_LIST_BOX_INTERVAL,
                        },
                    ),
                ],
                justify="start",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Label(html.B("Equipes IJCLab")),
                            dbc.Select(
                                id=ACTIVITY_TEAMS_LAB_TEAMS_ID,
                                html_size=ACTIVITY_TEAMS_LIST_MAX_SIZE,
                            ),
                        ],
                        width={"size": ACTIVITY_TEAMS_LIST_BOX_WIDTH, "offset": 0},
                        xxl={"size": ACTIVITY_TEAMS_LIST_BOX_WIDTH_XXL, "offset": 0},
                    ),
                    dbc.Col(
                        html.Div(
                            [
                                dbc.ButtonGroup(
                                    [
                                        dbc.Button(
                                            html.I(className="bi bi-chevron-double-right"),
                                            id=ACTIVITY_TEAMS_BUTTON_ADD_ID,
                                            disabled=True,
                                            style={"marginTop": "1em"},
                                        ),
                                        dbc.Button(
                                            html.I(className="bi bi-chevron-double-left"),
                                            id=ACTIVITY_TEAMS_BUTTON_REMOVE_ID,
                                            disabled=True,
                                            style={"marginTop": "2em"},
                                        ),
                                    ],
                                    vertical=True,
                                ),
                            ],
                            style={"display": "flex", "justifyContent": "center"},
                        ),
                        width=ACTIVITY_TEAMS_LIST_BOX_INTERVAL,
                        align="center",
                    ),
                    dbc.Col(
                        [
                            dbc.Label(html.B("Equipes du projet")),
                            dbc.Select(
                                id=ACTIVITY_TEAMS_SELECTED_TEAMS_ID,
                                html_size=ACTIVITY_TEAMS_LIST_MAX_SIZE,
                            ),
                        ],
                        width={"size": ACTIVITY_TEAMS_LIST_BOX_WIDTH, "offset": 0},
                        xxl={"size": ACTIVITY_TEAMS_LIST_BOX_WIDTH_XXL, "offset": 0},
                    ),
                ],
                justify="start",
                style={"marginTop": "5em"},
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Button(
                            "Mettre à jour",
                            id=ACTIVITY_TEAMS_BUTTON_UPDATE_ID,
                            disabled=True,
                        ),
                        width={"size": 3, "offset": 0},
                    ),
                    dbc.Col(
                        dbc.Button(
                            "Annuler",
                            id=ACTIVITY_TEAMS_BUTTON_CANCEL_ID,
                            disabled=True,
                        ),
                        width={"size": 3, "offset": 0},
                    ),
                ],
                justify="evenly",
                style={"marginTop": "3em"},
            ),
            dcc.Store(id=ACTIVITY_TEAMS_PROJECT_ACTIVITY_ID, data=True),
            dcc.Store(id=ACTIVITY_TEAMS_ADDED_TEAMS_ID, data=[]),
            dcc.Store(id=ACTIVITY_TEAMS_REMOVED_TEAMS_ID, data=[]),
            dcc.Store(id=ACTIVITY_TEAMS_RESET_INDICATOR_ID, data=0),
        ],
    )


def project_mgt_layout():
    """
    Build the layout for the project management tab.

    :return: html.Div component
    """

    masterproject_list = []
    project_list = []
    return html.Div(
        [
            html.P(),
            dbc.Alert(id=PROJECT_MGT_STATUS_ID, is_open=False),
            dbc.Row(
                [
                    dbc.RadioItems(
                        id=PROJECT_MGT_PROJECT_TYPE_ID,
                        options=[
                            {
                                "label": "Projets NSIP",
                                "value": PROJECT_MGT_PROJECT_TYPE_NSIP,
                            },
                            {
                                "label": "Projets locaux",
                                "value": PROJECT_MGT_PROJECT_TYPE_LOCAL,
                            },
                            {
                                "label": "Projets désactivés",
                                "value": PROJECT_MGT_PROJECT_TYPE_DISABLED,
                            },
                        ],
                        inline=True,
                    ),
                ],
                justify="center",
                style={"marginTop": "1em"},
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Label(html.B("Masterprojets")),
                            dbc.Select(
                                id=PROJECT_MGT_MASTERPROJECT_LIST_ID,
                                options=masterproject_list,
                                html_size=PROJECT_MGT_LIST_MAX_SIZE,
                            ),
                        ],
                        width={"size": PROJECT_MGT_LIST_BOX_WIDTH, "offset": 0},
                        xxl={"size": PROJECT_MGT_LIST_BOX_WIDTH_XXL, "offset": 0},
                    ),
                    dbc.Col(
                        [
                            dbc.Label(html.B("Projets")),
                            dbc.Select(
                                id=PROJECT_MGT_PROJECT_LIST_ID,
                                options=project_list,
                                html_size=PROJECT_MGT_LIST_MAX_SIZE,
                            ),
                        ],
                        width={"size": PROJECT_MGT_LIST_BOX_WIDTH, "offset": 0},
                        xxl={"size": PROJECT_MGT_LIST_BOX_WIDTH_XXL, "offset": 0},
                    ),
                ],
                style={"marginTop": "1em"},
            ),
            dbc.Row(
                dbc.Col(
                    dbc.Button(
                        "",
                        id=PROJECT_MGT_ACTION_BUTTON_ID,
                        disabled=True,
                        style={"visibility": "hidden"},
                    ),
                ),
                style={"marginTop": "3em"},
            ),
            dcc.Store(id=PROJECT_MGT_PROJECT_ACTIVITY_ID, data=True),
        ],
    )


def configuration_submenus():
    """
    Build the tabs menus of the configuration subapplication

    :return: DBC Tabs
    """

    global_params = GlobalParams()
    if AUTHORIZED_ROLES.index(global_params.session_data.role) > AUTHORIZED_ROLES.index(
        HITO_ROLE_PROJECT_MGR
    ):
        nsip_sync_disabled = True
        declaration_period_disabled = True
        project_mgt_disabled = True
    else:
        nsip_sync_disabled = False
        declaration_period_disabled = False
        project_mgt_disabled = False

    return dbc.Tabs(
        [
            dbc.Tab(
                id=TAB_ID_ACTIVITY_TEAMS,
                tab_id=TAB_ID_ACTIVITY_TEAMS,
                label="Equipes des projets",
            ),
            dbc.Tab(
                id=TAB_ID_NSIP_PROJECT_SYNC,
                tab_id=TAB_ID_NSIP_PROJECT_SYNC,
                label="Synchronisation NSIP",
                disabled=nsip_sync_disabled,
            ),
            dbc.Tab(
                id=TAB_ID_DECLARATION_PERIODS,
                tab_id=TAB_ID_DECLARATION_PERIODS,
                label="Périodes de déclaration",
                disabled=declaration_period_disabled,
            ),
            dbc.Tab(
                id=TAB_ID_PROJECT_MGT,
                tab_id=TAB_ID_PROJECT_MGT,
                label="Projets",
                disabled=project_mgt_disabled,
            ),
        ],
        id=CONFIGURATION_TAB_MENU_ID,
        persistence=True,
    )

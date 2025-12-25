"""
Functions to build tables associated with tab layouts
"""

import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
from dash import dcc, html
from flask import session

from ositah.apps.validation.parameters import (
    TABLE_COLUMN_VALIDATION,
    TABLE_ID_DECLARATION_STATS,
    TABLE_ID_MISSING_AGENTS,
    TABLE_ID_VALIDATION,
    VALIDATION_DECLARATIONS_SELECT_ALL,
    VALIDATION_DECLARATIONS_SELECT_NOT_VALIDATED,
    VALIDATION_DECLARATIONS_SELECT_VALIDATED,
)
from ositah.apps.validation.tools import (
    activity_time_cell,
    add_validation_declaration_selection_switch,
    agent_project_time,
    agent_tooltip_txt,
    category_declarations,
    define_declaration_thresholds,
    get_all_validation_status,
    validation_started,
)
from ositah.utils.agents import get_agents
from ositah.utils.exceptions import InvalidHitoProjectName, SessionDataMissing
from ositah.utils.menus import TABLE_TYPE_TABLE, build_accordion, ositah_jumbotron
from ositah.utils.projects import (
    CATEGORY_DEFAULT,
    DATA_SOURCE_HITO,
    DATA_SOURCE_OSITAH,
    get_team_projects,
    time_unit,
)
from ositah.utils.utils import (
    SEMESTER_WEEKS,
    TEAM_LIST_ALL_AGENTS,
    GlobalParams,
    general_error_jumbotron,
    no_session_id_jumbotron,
)


def build_validation_table(team, team_selection_date, declaration_set: int, period_date: str):
    """
    Build the agent list of the selected team with their declarations. Returns a table.

    :param team: selected team
    :param team_selection_date: last time the team selection was changed
    :param declaration_set: selected declaration set (all, validated or non-validated ones)
    :param period_date: a date that must be inside the declaration period
    :return: DBC table
    """
    global_params = GlobalParams()
    column_names = global_params.columns
    try:
        session_data = global_params.session_data
    except SessionDataMissing:
        return no_session_id_jumbotron()

    if session["user_email"] in global_params.roles["read-only"]:
        validation_disabled = True
    else:
        if session_data.role in global_params.validation_params["override_period"]:
            validation_disabled = False
        else:
            validation_disabled = not validation_started(period_date)

    validation_data = get_all_validation_status(period_date)
    define_declaration_thresholds(period_date)

    try:
        project_declarations = get_team_projects(
            team, team_selection_date, period_date, DATA_SOURCE_HITO
        )
    except InvalidHitoProjectName as e:
        return ositah_jumbotron(
            "Error loading projects",
            e.msg,
            title_class="text-danger",
        )

    if project_declarations is None:
        return html.Div(
            [
                dbc.Alert(
                    f"Aucune déclaration effectuée pour l'équipe '{team}'",
                    color="warning",
                ),
            ]
        )
    declarations = category_declarations(project_declarations)

    if team == TEAM_LIST_ALL_AGENTS:
        declaration_list = declarations
    else:
        declaration_list = declarations[declarations[column_names["team"]].str.match(team)]
    declaration_list["validation_disabled"] = validation_disabled

    data_columns = [CATEGORY_DEFAULT]
    data_columns.extend(global_params.project_categories.keys())

    try:
        validated_project_declarations = get_team_projects(
            team, team_selection_date, period_date, DATA_SOURCE_OSITAH, use_cache=False
        )
    except InvalidHitoProjectName as e:
        return ositah_jumbotron(
            "Error loading projects",
            e.msg,
            title_class="text-danger",
        )

    if validated_project_declarations is None:
        declaration_list["validated"] = False
        declaration_list["hito_missing"] = False
        validated_declarations_num = 0
        hito_missing_num = 0
        hito_missing_msg = ""
    else:
        validated_declarations_num = len(validated_project_declarations)
        validated_declarations = category_declarations(
            validated_project_declarations, use_cache=False
        )
        # Do an outer merge to detect validated declarations removed from Hito
        declaration_list = declaration_list.merge(
            validated_declarations,
            how="outer",
            on=column_names["agent_id"],
            indicator=True,
            suffixes=[None, "_val"],
        )
        declaration_list["validated"] = (declaration_list._merge == "both") | (
            declaration_list._merge == "right_only"
        )
        declaration_list["hito_missing"] = declaration_list._merge == "right_only"
        hito_missing_num = len(declaration_list.loc[declaration_list["hito_missing"]])
        if hito_missing_num > 0:
            columns_fillna = {c: 0 for c in [*data_columns, "total_hours", "percent_global"]}
            declaration_list.loc[declaration_list["hito_missing"]] = declaration_list.fillna(
                value=columns_fillna
            )
            declaration_list.loc[declaration_list["hito_missing"], column_names["fullname"]] = (
                declaration_list[f"{column_names['fullname']}_val"]
            )
            declaration_list.loc[declaration_list["hito_missing"], column_names["team"]] = (
                declaration_list[f"{column_names['team']}_val"]
            )
            declaration_list.loc[declaration_list["hito_missing"], "suspect"] = True
            declaration_list.loc[declaration_list["hito_missing"], "validation_disabled"] = True
            declaration_list.sort_values(by=column_names["fullname"], inplace=True)
            hito_missing_msg = (
                f" dont {hito_missing_num} supprimé"
                f"{'s' if hito_missing_num > 1 else ''} de Hito"
            )
        else:
            hito_missing_msg = ""
        for category in data_columns:
            time_ok_column = f"{category}_time_ok"
            declaration_list.loc[declaration_list.validated, time_ok_column] = np.isclose(
                declaration_list.loc[declaration_list.validated, category],
                declaration_list.loc[declaration_list.validated, f"{category}_val"],
                rtol=1e-5,
                atol=0,
            )
    validated_number = len(declaration_list[declaration_list["validated"]])

    if declaration_set == VALIDATION_DECLARATIONS_SELECT_ALL:
        selected_declarations = declaration_list
    elif declaration_set == VALIDATION_DECLARATIONS_SELECT_VALIDATED:
        selected_declarations = declaration_list[declaration_list["validated"]]
    elif declaration_set == VALIDATION_DECLARATIONS_SELECT_NOT_VALIDATED:
        selected_declarations = declaration_list[~declaration_list["validated"]]
    else:
        return general_error_jumbotron(f"Invalid declaration set ID ({declaration_set})")
    selected_declarations.sort_values(by=["fullname"], ignore_index=True, inplace=True)

    columns = [*data_columns]
    columns.insert(0, column_names["fullname"])
    columns.append("percent_global")
    rows_number = len(selected_declarations)

    table_header = [
        html.Thead(
            html.Tr(
                [
                    *[
                        html.Th(
                            [
                                html.Div(
                                    [
                                        html.I(f"{global_params.column_titles[c]} "),
                                    ]
                                ),
                                html.Div(time_unit(c, english=False, parenthesis=True)),
                            ],
                            className="text-center",
                        )
                        for c in columns
                    ],
                    html.Th(TABLE_COLUMN_VALIDATION),
                ],
            )
        )
    ]

    table_body = [
        html.Tbody(
            [
                html.Tr(
                    [
                        html.Td(
                            build_accordion(
                                i,
                                selected_declarations.iloc[i - 1][column_names["fullname"]],
                                agent_project_time(
                                    selected_declarations.iloc[i - 1][column_names["fullname"]]
                                ),
                                agent_tooltip_txt(selected_declarations.iloc[i - 1], data_columns),
                                (
                                    "validated_hito_missing"
                                    if selected_declarations.iloc[i - 1]["hito_missing"]
                                    else ""
                                ),
                            ),
                            className="accordion",
                            key=f"validation-table-cell-{i}-fullname",
                        ),
                        *[
                            activity_time_cell(selected_declarations.iloc[i - 1], c, i)
                            for c in data_columns
                        ],
                        activity_time_cell(selected_declarations.iloc[i - 1], "percent_global", i),
                        html.Td(
                            [
                                dbc.Checklist(
                                    options=[
                                        {
                                            "label": "",
                                            "value": 1,
                                            "disabled": selected_declarations.iloc[i - 1][
                                                "validation_disabled"
                                            ],
                                        }
                                    ],
                                    value=[
                                        int(
                                            selected_declarations.iloc[i - 1][
                                                column_names["agent_id"]
                                            ]
                                            in validation_data.index
                                        )
                                    ],
                                    id={"type": "validation-switch", "id": i},
                                    key=f"validation-switch-{i}",
                                    switch=True,
                                ),
                                # The dcc.Store is created to ease validation callback management
                                # by passing the agent ID and providing an Output object (but
                                # nothing will be written in it).
                                dcc.Store(
                                    id={"type": "validation-agent-id", "id": i},
                                    data=selected_declarations.iloc[i - 1][
                                        column_names["agent_id"]
                                    ],
                                ),
                            ],
                            className="align-middle",
                            key=f"validation-table-cell-{i}-switch",
                        ),
                    ],
                    key=f"validation-table-row-{i}",
                )
                for i in range(1, rows_number + 1)
            ]
        )
    ]

    return html.Div(
        [
            dbc.Alert(
                [
                    html.Div(
                        html.B(
                            (
                                f"Nombre d'agents de l'équipe '{team}' ayant déclaré :"
                                f" {len(selected_declarations)} (agents validés={validated_number}"
                                f"{hito_missing_msg}"
                                f", déclarations validées/totales="
                                f"{validated_declarations_num}/{len(project_declarations)})"
                            ),
                            className="agent_count",
                        )
                    ),
                    html.Div(
                        html.Em(
                            (
                                f"Temps déclarés de l'équipe / total ="
                                f" {round(selected_declarations['percent_global'].mean(), 1)}%"
                                f" (100%={SEMESTER_WEEKS} semaines)"
                            )
                        )
                    ),
                ]
            ),
            html.P(),
            add_validation_declaration_selection_switch(declaration_set),
            dbc.Table(
                table_header + table_body,
                id={"type": TABLE_TYPE_TABLE, "id": TABLE_ID_VALIDATION},
                bordered=True,
                hover=True,
                striped=True,
                class_name="sortable",
            ),
        ]
    )


def build_missing_agents_table(team, team_selection_date, period_date: str):
    """
    Function to build a table listing all agents that have not declared yet their time on projects

    :param team: selected team
    :param team_selection_date: last time the team selection was changed
    :param period_date: a date that must be inside the declaration period
    :return: missing agent page
    """
    global_params = GlobalParams()
    column_names = global_params.columns
    declaration_options = global_params.declaration_options

    try:
        declarations = get_team_projects(team, team_selection_date, period_date)
    except InvalidHitoProjectName as e:
        return ositah_jumbotron(
            "Error loading projects",
            e.msg,
            title_class="text-danger",
        )

    agent_list = get_agents(period_date, team)

    if declarations is None:
        missing_agents = agent_list
    else:
        missing_agents = build_missing_agents(declarations, agent_list)

    rows_number = len(missing_agents)
    table_columns = ["fullname", "team"]

    table_header = [
        html.Thead(
            html.Tr(
                [
                    html.Th(
                        [
                            html.I(f"{global_params.column_titles[c]} "),
                        ]
                    )
                    for c in table_columns
                ],
            )
        )
    ]

    table_body = [
        html.Tbody(
            [
                html.Tr(
                    [
                        html.Td(
                            missing_agents.iloc[i][column_names[c]],
                            className="align-middle",
                        )
                        for c in table_columns
                    ]
                )
                for i in range(rows_number)
            ]
        )
    ]

    return html.Div(
        [
            dbc.Alert(
                [
                    html.Div(
                        html.B(
                            (
                                f"Nombre d'agents de l'équipe '{team}' sans déclaration :"
                                f" {len(missing_agents)}"
                            )
                        )
                    ),
                    html.Div(
                        html.Em(
                            (
                                f"Statuts non inclus :"
                                f" {', '.join(declaration_options['optional_statutes'])}"
                            )
                        )
                    ),
                    html.Div(
                        html.Em(
                            (
                                f"Equipes non incluses :"
                                f" {', '.join(declaration_options['optional_teams'])}"
                            )
                        )
                    ),
                ],
                class_name="agent_count",
            ),
            html.P(),
            dbc.Table(
                table_header + table_body,
                id={"type": TABLE_TYPE_TABLE, "id": TABLE_ID_MISSING_AGENTS},
                bordered=True,
                hover=True,
                striped=True,
                class_name="sortable",
            ),
        ]
    )


def build_statistics_table(team, team_selection_date, period_date: str):
    """
    Function to build a table listing the number of declarations and missing declarations per team

    :param team: selected team
    :param team_selection_date: last time the team selection was changed
    :param period_date: a date that must be inside the declaration period
    :return: missing agent page
    """
    global_params = GlobalParams()
    column_names = global_params.columns
    declaration_options = global_params.declaration_options

    try:
        session_data = global_params.session_data
    except SessionDataMissing:
        return no_session_id_jumbotron()

    try:
        declarations = get_team_projects(team, team_selection_date, period_date)
    except InvalidHitoProjectName as e:
        return ositah_jumbotron(
            "Error loading projects",
            e.msg,
            title_class="text-danger",
        )

    agent_list = get_agents(period_date, team)

    add_no_team_row = False
    if declarations is None:
        team_declarations = pd.DataFrame({"declarations_number": 0}, index=[team])
        team_declarations["missings_number"] = len(agent_list)
        missing_declarations = pd.DataFrame()
    else:
        team_agent_declarations = declarations.drop_duplicates(
            subset=[column_names["team"], column_names["fullname"]]
        )
        # If team is None, set it to empty string
        if len(team_agent_declarations.loc[team_agent_declarations.team.isna(), "team"]) > 0:
            team_agent_declarations.loc[team_agent_declarations.team.isna(), "team"] = ""
            add_no_team_row = True
        team_declarations = (
            team_agent_declarations[column_names["team"]]
            .value_counts()
            .to_frame(name="declarations_number")
        )

        missing_agents = build_missing_agents(declarations, agent_list)
        missing_declarations = (
            missing_agents[column_names["team"]].value_counts().to_frame(name="missings_number")
        )
        # If team is None, set it to empty string
        if len(missing_declarations.loc[missing_declarations.index == ""]) > 0:
            add_no_team_row = True

    team_list = pd.DataFrame(index=session_data.agent_teams)
    if team == TEAM_LIST_ALL_AGENTS:
        team_list.drop(index=TEAM_LIST_ALL_AGENTS, inplace=True)
        if add_no_team_row:
            team_list = pd.concat([team_list, pd.DataFrame(index=[""])])
    else:
        team_list = team_list[team_list.index.str.match(team)]
    team_agents = agent_list[column_names["team"]].value_counts().to_frame(name="agents_number")
    team_declarations = pd.merge(
        team_declarations,
        team_list,
        how="outer",
        left_index=True,
        right_index=True,
        sort=True,
    ).fillna(0)
    team_declarations = pd.merge(team_declarations, team_agents, left_index=True, right_index=True)

    if len(missing_declarations):
        team_declarations = pd.merge(
            team_declarations,
            missing_declarations,
            how="outer",
            left_index=True,
            right_index=True,
            sort=True,
        ).fillna(0)
    else:
        team_declarations["missings_number"] = 0

    declarations_total = int(sum(team_declarations["declarations_number"]))
    missings_total = int(sum(team_declarations["missings_number"]))

    data_columns = ["declarations_number", "missings_number"]

    table_header = [
        html.Thead(
            html.Tr(
                [
                    html.Th(
                        [
                            html.I(f"{global_params.column_titles['team']} "),
                        ]
                    ),
                    *[
                        html.Th(
                            html.Div(
                                [
                                    html.I(f"{global_params.column_titles[c]} "),
                                ]
                            ),
                            className="text-center",
                        )
                        for c in data_columns
                    ],
                ],
            )
        )
    ]

    table_body = [
        html.Tbody(
            [
                html.Tr(
                    [
                        html.Td(i),
                        *[
                            html.Td(
                                team_declarations.loc[i, column_names[c]],
                                className="text-center",
                            )
                            for c in data_columns
                        ],
                    ]
                )
                for i in team_declarations.index.values
            ]
        )
    ]

    return html.Div(
        [
            dbc.Alert(
                [
                    html.Div(
                        html.B(
                            (
                                f"Statistiques des déclarations pour l'équipe '{team}' :"
                                f" effectuées={declarations_total}, manquantes={missings_total}"
                            )
                        )
                    ),
                    html.Div(
                        html.Em(
                            (
                                f"Statuts non inclus dans les déclarations manquantes :"
                                f" {', '.join(declaration_options['optional_statutes'])}"
                            )
                        )
                    ),
                    html.Div(
                        html.Em(
                            (
                                f"Equipes non incluses dans les déclarations manquantes :"
                                f" {', '.join(declaration_options['optional_teams'])}"
                            )
                        )
                    ),
                ],
                class_name="agent_count",
            ),
            html.P(),
            dbc.Table(
                table_header + table_body,
                id={"type": TABLE_TYPE_TABLE, "id": TABLE_ID_DECLARATION_STATS},
                bordered=True,
                hover=True,
                striped=True,
                class_name="sortable",
            ),
        ]
    )


def build_missing_agents(declarations, agents, mandatory_only: bool = True):
    """
    Build the missing agents list and return it as a dataframe. It allows not toking into
    consideration the agent declarations for agents whose declaration is not mandatory
    (e.g. fellows).

    :param declarations: project declarations
    :param agents: list of agents who are supposed to do a declaration
    :param mandatory_only: ignore agents whose declaration is optional
    :return: missing agents dataframe
    """

    global_params = GlobalParams()
    column_names = global_params.columns

    declared_agents = pd.DataFrame(
        {column_names["agent_id"]: declarations[column_names["agent_id"]].unique()}
    )
    if mandatory_only:
        agent_list = agents[~agents.optional]
    else:
        agent_list = agents
    missing_agents = pd.merge(
        agent_list,
        declared_agents,
        on=column_names["agent_id"],
        how="outer",
        indicator=True,
    )
    missing_agents = missing_agents[missing_agents._merge == "left_only"].sort_values(
        by=column_names["fullname"]
    )

    return missing_agents

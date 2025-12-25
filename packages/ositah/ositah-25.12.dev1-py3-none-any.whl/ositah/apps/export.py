# OSITAH sub-application exporting data to NSIP
import math
import re

import dash_bootstrap_components as dbc
import numpy as np
from dash import dcc, html
from dash.dependencies import ALL, MATCH, Input, Output, State
from dash.exceptions import PreventUpdate

from ositah.app import app
from ositah.utils.agents import get_agents, get_nsip_agents
from ositah.utils.exceptions import SessionDataMissing
from ositah.utils.menus import (
    DATA_SELECTED_SOURCE_ID,
    TABLE_TYPE_TABLE,
    TEAM_SELECTED_VALUE_ID,
    TEAM_SELECTION_DATE_ID,
    VALIDATION_PERIOD_SELECTED_ID,
    create_progress_bar,
    team_list_dropdown,
)
from ositah.utils.period import get_validation_period_dates
from ositah.utils.projects import (
    DATA_SOURCE_OSITAH,
    category_time_and_unit,
    get_hito_projects,
    get_nsip_declarations,
    get_team_projects,
)
from ositah.utils.utils import (
    HITO_ROLE_PROJECT_MGR,
    HITO_ROLE_SUPER_ADMIN,
    NSIP_COLUMN_NAMES,
    TEAM_LIST_ALL_AGENTS,
    TIME_UNIT_HOURS_EN,
    GlobalParams,
    no_session_id_jumbotron,
)

EXPORT_TAB_MENU_ID = "report-tabs"
TAB_ID_EXPORT_NSIP = "nsip-export-page"
TAB_MENU_EXPORT_NSIP = "Export NSIP"

TABLE_NSIP_EXPORT_ID = "export-nsip"

NSIP_EXPORT_BUTTON_LABEL = "Export"
NSIP_EXPORT_BUTTON_ID = "export-nsip-selected-users"
NSIP_EXPORT_SELECT_ALL_ID = "export-nsip-select-all"
NSIP_EXPORT_ALL_SELECTED_ID = "export-nsip-all-selected"
NSIP_EXPORT_STATUS_ID = "export-nsip-status-msg"
NSIP_EXPORT_SELECTION_STATUS_ID = "export-nsip-selection-update-status"

EXPORT_LOAD_INDICATOR_ID = "export-nsip-load-indicator"
EXPORT_SAVED_LOAD_INDICATOR_ID = "export-nsip-saved-load-indicator"
EXPORT_LOAD_TRIGGER_INTERVAL_ID = "export-nsip-load-callback-interval"
EXPORT_MAX_FAILDED_UPDATES = 30
EXPORT_PROGRESS_BAR_MAX_DURATION = 8  # seconds
EXPORT_SAVED_ACTIVE_TAB_ID = "export-nsip-saved-active-tab"

EXPORT_NSIP_SYNC_INDICATOR_ID = "export-nsip-sync-indicator"
EXPORT_NSIP_SAVED_SYNC_INDICATOR_ID = "export-nsip-saved-sync-indicator"
EXPORT_NSIP_SYNC_FREQUENCY = 2.0  # Average number of sync operations per second
EXPORT_NSIP_SYNC_TRIGGER_INTERVAL_ID = "export-nsip-sync-callback-interval"
EXPORT_NSIP_MULTIPLE_CONTRACTS_ERROR = re.compile(
    (
        r'"Agent has active multi-contracts in same laboratory - manual action needed\s+'
        r"\|\s+idAgentContract\s+:\s+(?P<id1>\d+)\s+\|\s+idAgentContract\s+:\s+(?P<id2>\d+)"
    )
)

NSIP_DECLARATIONS_SELECT_ALL = 0
NSIP_DECLARATIONS_SELECT_UNSYNCHRONIZED = 1
NSIP_DECLARATIONS_SWITCH_ID = "export-nsip-declaration-set-switch"
NSIP_DECLARATIONS_SELECTED_ID = "export-nsip-selected-declaration-set"


def export_submenus():
    """
    Build the tabs menus of the export subapplication

    :return: DBC Tabs
    """

    return dbc.Tabs(
        [
            dbc.Tab(
                id=TAB_ID_EXPORT_NSIP,
                tab_id=TAB_ID_EXPORT_NSIP,
                label=TAB_MENU_EXPORT_NSIP,
            ),
            dcc.Store(id=NSIP_DECLARATIONS_SELECTED_ID, data=NSIP_DECLARATIONS_SELECT_ALL),
        ],
        id=EXPORT_TAB_MENU_ID,
    )


def export_layout():
    """
    Build the layout for this application, after reading the data if necessary.

    :return: application layout
    """

    return html.Div(
        [
            html.H1("Export des déclarations vers NSIP"),
            team_list_dropdown(),
            # The following dcc.Store is used to ensure that the the ijclab_export input exists
            # before the export page is created
            dcc.Store(id=DATA_SELECTED_SOURCE_ID, data=DATA_SOURCE_OSITAH),
            html.Div(export_submenus(), id="export-submenus", style={"marginTop": "3em"}),
            dcc.Store(id=EXPORT_LOAD_INDICATOR_ID, data=0),
            dcc.Store(id=EXPORT_SAVED_LOAD_INDICATOR_ID, data=0),
            dcc.Store(id=EXPORT_SAVED_ACTIVE_TAB_ID, data=""),
        ]
    )


def nsip_export_table(team, team_selection_date, period_date: str, declarations_set):
    """
    Build a table ready to be exported to NSIP from validated declarations. The produced table
    can then be exported as a CSV for ingestion by NSIP.

    :param team: selected team
    :param team_selection_date: last time the team selection was changed
    :param period_date: a date that must be inside the declaration period
    :param declarations_set: declaration set to use (all or only non-synchronized)
    :return: dbc.Table
    """

    if team is None:
        return html.Div("")

    global_params = GlobalParams()
    columns = global_params.columns
    try:
        session_data = global_params.session_data
    except SessionDataMissing:
        return no_session_id_jumbotron()

    start_date, end_date = get_validation_period_dates(period_date)

    if session_data.role in [HITO_ROLE_PROJECT_MGR, HITO_ROLE_SUPER_ADMIN]:
        export_disabled = False
    else:
        export_disabled = True

    if session_data.nsip_declarations is None:
        hito_projects = get_hito_projects()
        declaration_list = get_team_projects(
            team, team_selection_date, period_date, DATA_SOURCE_OSITAH
        )
        if declaration_list is None or declaration_list.empty:
            return dbc.Alert(
                f"Aucune données validées n'existe pour l'équipe '{team}'",
                color="warning",
            )
        ositah_total_declarations_num = len(declaration_list)
        declaration_list = declaration_list.merge(
            hito_projects,
            left_on="hito_project_id",
            right_on="id",
            suffixes=[None, "_y"],
        )
        agent_list = get_agents(period_date, team)
        if team is None or team == TEAM_LIST_ALL_AGENTS:
            # If no team is selected, merge left to include declarations from agents whose
            # email_auth don't match between Hito and NSIP. It is typically the case for agents
            # who are no longer active in NSIP (e.g. agents who left the lab during the
            # declaration period).
            merge_how = "left"
        else:
            merge_how = "inner"
        declaration_list = declaration_list.merge(
            agent_list,
            how=merge_how,
            left_on=columns["agent_id"],
            right_on="id",
            suffixes=[None, "_y"],
        )
        declaration_list[["time", "time_unit"]] = declaration_list.apply(
            lambda r: category_time_and_unit(r["category"], r[columns["hours"]], english=True),
            axis=1,
            result_type="expand",
        )
        declaration_list["time"] = declaration_list["time"].astype(int, copy=False)
        declaration_list["email_auth"] = declaration_list["email_auth"].str.lower()
        declaration_list.sort_values(by="email_auth", inplace=True)

        colums_to_delete = []
        for columnn in declaration_list.columns.to_list():
            if columnn not in [
                *NSIP_COLUMN_NAMES.keys(),
                columns["statut"],
                columns["cem"],
                "fullname",
            ]:
                colums_to_delete.append(columnn)
        if len(colums_to_delete) > 0:
            declaration_list.drop(columns=colums_to_delete, inplace=True)

        nsip_agents = get_nsip_agents()
        declaration_list = declaration_list.merge(
            nsip_agents,
            how="left",
            left_on="email_auth",
            right_on="email_reseda",
            suffixes=[None, "_nsipa"],
            indicator=True,
        )

        # For OSITAH entries not found in NSIP, it may be that the agent left the lab during
        # the declaration period: in this case there is an entry in NSIP where the RESEDA email
        # has been replaced by a UUID allowing to update NSIP data. Check if such an entry
        # exists in NSIP with a matching fullname and use it if it exists. It also happens if the
        # agent email_auth changed during the period.
        # To make matching easier, index is temporarily set to fullname instead of an integer.
        nsip_missing_agent_names = declaration_list.loc[
            declaration_list["_merge"] == "left_only", columns["fullname"]
        ].unique()
        declaration_list.set_index(columns["fullname"], inplace=True)
        nsip_agents.set_index(columns["fullname"], inplace=True)
        for name in nsip_missing_agent_names:
            if name in nsip_agents.index:
                matching_inactive_nsip_agent = nsip_agents.loc[[name]]
                if not matching_inactive_nsip_agent.empty:
                    # Should always work, raise an exception if it is not the case
                    declaration_list.update(matching_inactive_nsip_agent, errors="raise")
                    # Mark the entry as complete
                    declaration_list.loc[name, "_merge"] = "both"
        declaration_list.reset_index(inplace=True)

        declaration_list["nsip_agent_missing"] = declaration_list["_merge"] == "left_only"
        declaration_list["optional"] = declaration_list[columns["statut"]].isin(
            global_params.declaration_options["optional_statutes"]
        )

        # For EC (enseignant chercheurs), apply the ratio defined in the configuration (if any)
        # to teaching hours declared to convert them into hours with students
        if global_params.teaching_ratio:
            ratio = global_params.teaching_ratio["ratio"]
            cem = global_params.teaching_ratio["cem"]
            if cem:
                declaration_list.loc[
                    (declaration_list.nsip_master == global_params.teaching_ratio["masterproject"])
                    & (declaration_list[columns["cem"]].isin(cem)),
                    "time",
                ] = np.round(declaration_list["time"] / ratio)
            else:
                declaration_list.loc[
                    declaration_list.nsip_master == global_params.teaching_ratio["masterproject"],
                    "time",
                ] = np.round(declaration_list["time"] / ratio)

        # Check that the number of hours doesn't exceed the maximum allowed for activities
        # declared in hours
        declaration_list["invalid_time"] = False
        declaration_list.loc[
            declaration_list["time_unit"] == TIME_UNIT_HOURS_EN, "invalid_time"
        ] = (declaration_list["time"] > global_params.declaration_options["max_hours"])
        declaration_list.drop(columns="_merge", inplace=True)

        nsip_declarations = get_nsip_declarations(start_date, team)
        if nsip_declarations.empty:
            # nsip_missing is True if the OSITAH declaration has no matching declaration in NSIP
            declaration_list["nsip_missing"] = True
            # time_unit_mismatch is True only if there is a matching declaration in NSIP and time
            # unit differs
            declaration_list["time_unit_mismatch"] = False
            # mgr_val_time_mismatch indicates that validation time is different in OSITAH and NSIP
            declaration_list["mgr_val_time_mismatch"] = False
            # nsip_inconsistency is True only if there is a matching declaration in NSIP and
            # time differs
            declaration_list["nsip_inconsistency"] = False
            # ositah_missing is True if a declaratipn is found in NSIP without a matching
            # declaration in OSITAH
            declaration_list["ositah_missing"] = False
            # Other columns expected by the code below
            declaration_list["id_declaration"] = np.NaN
        else:
            declaration_list["nsip_project_id"] = declaration_list["nsip_project_id"].astype(int)
            declaration_list["nsip_reference_id"] = declaration_list["nsip_reference_id"].astype(
                int
            )
            # In case nsip_declarations contains only references (no project), create the
            # project.name column required later as it is used both for references and projects.
            # Also copy reference.name into project.name if it is a reference.
            if "project.name" not in nsip_declarations:
                nsip_declarations["project.name"] = np.NaN
            if "reference.name" not in nsip_declarations:
                nsip_declarations["reference.name"] = np.NaN
            nsip_declarations.loc[
                nsip_declarations["project.name"].isna(),
                "nsip_project",
            ] = nsip_declarations["reference.name"]
            # Merge OSITAH declarations with those possibly present in NSIP
            declaration_list = declaration_list.merge(
                nsip_declarations,
                how="outer",
                left_on=["email_reseda", "nsip_project_id", "nsip_reference_id"],
                right_on=["agent.email", "project.id", "reference.id"],
                suffixes=[None, "_nsipd"],
                indicator=True,
            )
            # Merge all declarations for an agent related to the same NSIP activity, if several
            # local activities are associated with one NSIP one. First build the list of distinct
            # NSIP activities and aggregate the related time, then merge back this time in the
            # declaration list.
            nsip_activity_identifier = [
                "agent.id",
                "project.id",
                "reference.id",
                "email_auth",
                "nsip_project_id",
                "nsip_reference_id",
            ]
            for c in nsip_activity_identifier:
                if declaration_list.dtypes[c] == "object":
                    declaration_list.loc[declaration_list[c].isna(), c] = ""
                else:
                    declaration_list.loc[declaration_list[c].isna(), c] = 0
            combined_declarations = (
                declaration_list[[*nsip_activity_identifier, "time"]]
                .groupby(by=nsip_activity_identifier, as_index=False, sort=False)
                .sum()
            )
            declaration_list = declaration_list.drop(columns="time").drop_duplicates(
                nsip_activity_identifier
            )
            declaration_list = declaration_list.merge(
                combined_declarations,
                how="inner",
                on=nsip_activity_identifier,
                suffixes=[None, "_cd"],
            )
            # time_unit_mismatch is True only if there is a matching declaration in NSIP and time
            # unit differs
            declaration_list["time_unit_mismatch"] = False
            declaration_list.loc[declaration_list["_merge"] == "both", "time_unit_mismatch"] = (
                declaration_list.loc[declaration_list["_merge"] == "both", "time_unit"]
                != declaration_list.loc[declaration_list["_merge"] == "both", "volume"]
            )
            # nsip_inconsistency is True only if there is a matching declaration in NSIP and
            # time differs
            declaration_list["nsip_inconsistency"] = False
            declaration_list.loc[declaration_list["_merge"] == "both", "nsip_inconsistency"] = (
                declaration_list.loc[declaration_list["_merge"] == "both", "time"]
                != declaration_list.loc[declaration_list["_merge"] == "both", "time_nsipd"]
            )
            # mgr_val_time_mismatch is True only if there is a matching declaration in NSIP and
            # manager validation time differs
            declaration_list["mgr_val_time_mismatch"] = False
            declaration_list.loc[
                declaration_list["_merge"] == "both", "mgr_val_time_mismatch"
            ] = declaration_list[declaration_list["_merge"] == "both"].apply(
                lambda r: (
                    False
                    if r["managerValidationDate"]
                    and re.match(
                        r["managerValidationDate"], r["validation_time"].date().isoformat()
                    )
                    else True
                ),
                axis=1,
            )
            # nsip_missing is True if the OSITAH declaration has no matching declaration in NSIP
            declaration_list["nsip_missing"] = declaration_list["_merge"] == "left_only"
            # ositah_missing is True if a declaration is found in NSIP without a matching
            # declaration in OSITAH
            declaration_list["ositah_missing"] = declaration_list["_merge"] == "right_only"
            for ositah_column, nsip_column in {
                "email_auth": "agent.email",
                "fullname": "nsip_fullname",
                "nsip_project_id": "project.id",
                "nsip_reference_id": "reference.id",
                "nsip_project": "project.name",
                "time": "time_nsipd",
                "time_unit": "volume",
            }.items():
                declaration_list.loc[declaration_list["ositah_missing"], ositah_column] = (
                    declaration_list[nsip_column]
                )
            declaration_list.loc[
                declaration_list["nsip_agent_missing"].isna(), "nsip_agent_missing"
            ] = False
            declaration_list.drop(columns="_merge", inplace=True)

        # Mark declarations that are properly synced between OSITAH and NSIP for easier
        # processing later
        declaration_list["declaration_ok"] = ~declaration_list[
            [
                "nsip_missing",
                "nsip_inconsistency",
                "ositah_missing",
                "nsip_missing",
                "mgr_val_time_mismatch",
                "invalid_time",
            ]
        ].any(axis=1)

        # Define declarations that be selected for NSIP synchronisation as all declarations that
        # are not ok, except those corresponding to agents missing in NSIP or that have no
        # matching entries in OSITAH
        if export_disabled:
            declaration_list["selectable"] = False
        else:
            declaration_list["selectable"] = ~declaration_list["declaration_ok"]
            declaration_list.loc[
                declaration_list["selectable"] & declaration_list["ositah_missing"],
                "selectable",
            ] = False
            declaration_list.loc[
                declaration_list["selectable"] & declaration_list["invalid_time"],
                "selectable",
            ] = False
            declaration_list.loc[
                declaration_list["selectable"] & declaration_list["nsip_agent_missing"],
                "selectable",
            ] = False
            declaration_list.loc[
                declaration_list["selectable"]
                & (declaration_list["nsip_project_id"] == 0)
                & (declaration_list["nsip_reference_id"] == 0),
                "selectable",
            ] = False

        # Reset selected state to False
        declaration_list["selected"] = False
        # Rset nsip_project_id and nsip_reference_id to NaN if they are equal to 0 so that the
        # corresponding cell is empty
        declaration_list.loc[declaration_list["nsip_project_id"] == 0, "nsip_project_id"] = np.NaN
        declaration_list.loc[declaration_list["nsip_reference_id"] == 0, "nsip_reference_id"] = (
            np.NaN
        )

        # Sort declarations by email_auth and add index value as column for easier further
        # processing
        declaration_list.sort_values(by="email_auth", inplace=True)
        declaration_list["row_index"] = declaration_list.index

        session_data.nsip_declarations = declaration_list

    else:
        declaration_list = session_data.nsip_declarations
        ositah_total_declarations_num = session_data.total_declarations_num

    declarations_ok = declaration_list[declaration_list["declaration_ok"]]
    declarations_ok_num = len(declarations_ok)
    agents_ok_num = len(declarations_ok["email_auth"].unique())
    nsip_agent_missing_num = len(
        declaration_list.loc[declaration_list["nsip_agent_missing"], "email_auth"].unique()
    )
    nsip_optional_missing_num = len(
        declaration_list.loc[
            declaration_list["nsip_agent_missing"] & declaration_list["optional"],
            "email_auth",
        ].unique()
    )
    ositah_missing_num = len(declaration_list[declaration_list["ositah_missing"]])
    ositah_validated_declarations_num = len(declaration_list) - ositah_missing_num
    page_title = [
        html.Div(
            (
                f"Export NSIP des contributions validées de '{team}' du"
                f" {start_date.strftime('%Y-%m-%d')} au {end_date.strftime('%Y-%m-%d')}"
            )
        ),
        html.Div(
            (
                f"Déclarations totales={ositah_total_declarations_num} dont"
                f"  synchronisées/validées={declarations_ok_num}/"
                f"{ositah_validated_declarations_num}, "
                f" manquantes OSITAH={ositah_missing_num}"
            )
        ),
        html.Div(
            (
                f"(agents synchronisés={agents_ok_num},"
                f" agents manquants dans NSIP={nsip_agent_missing_num} dont"
                f" optionnels={nsip_optional_missing_num})"
            )
        ),
    ]
    if team and team != TEAM_LIST_ALL_AGENTS:
        page_title.append(
            html.Div(
                (
                    "Certains agents peuvent apparaitre non synchronisés s'ils ont quitté"
                    f" le laboratoire: utiliser '{TEAM_LIST_ALL_AGENTS}' pour vérifier"
                ),
                style={"fontStyle": "italic", "fontWeight": "bold"},
            )
        )

    if declarations_set == NSIP_DECLARATIONS_SELECT_ALL:
        selected_declarations = declaration_list
    else:
        selected_declarations = declaration_list[~declaration_list["declaration_ok"]]

    data_columns = list(NSIP_COLUMN_NAMES.keys())
    data_columns.remove("email_auth")

    table_header = [
        html.Thead(
            html.Tr(
                [
                    html.Th(
                        [
                            (
                                dbc.Checkbox(id=NSIP_EXPORT_SELECT_ALL_ID)
                                if selected_declarations["selectable"].any()
                                else html.Div()
                            ),
                            dcc.Store(id=NSIP_EXPORT_ALL_SELECTED_ID, data=0),
                        ]
                    ),
                    html.Th("email_reseda"),
                    *[html.Th(c) for c in data_columns],
                ]
            )
        )
    ]

    table_body = []
    for email in selected_declarations["email_auth"].unique():
        tr_list = nsip_build_user_declarations(selected_declarations, email, data_columns)
        table_body.extend(tr_list)
    table_body = [html.Tbody(table_body)]

    return html.Div(
        [
            html.Div(
                [
                    dbc.Row(
                        [
                            dbc.Col(dbc.Alert(page_title), width=10),
                            dbc.Col(
                                [
                                    dbc.Button(
                                        NSIP_EXPORT_BUTTON_LABEL,
                                        id=NSIP_EXPORT_BUTTON_ID,
                                        disabled=True,
                                    ),
                                ],
                                width={"size": 1, "offset": 1},
                            ),
                        ]
                    ),
                ]
            ),
            add_nsip_declaration_selection_switch(declarations_set),
            html.Div(
                dbc.Col(
                    dbc.Alert(dismissable=True, is_open=False, id=NSIP_EXPORT_STATUS_ID),
                    width=9,
                )
            ),
            dcc.Store(id=NSIP_EXPORT_SELECTION_STATUS_ID, data=0),
            dcc.Store(id=EXPORT_NSIP_SYNC_INDICATOR_ID, data=0),
            dcc.Store(id=EXPORT_NSIP_SAVED_SYNC_INDICATOR_ID, data=0),
            html.P(""),
            dbc.Table(
                table_header + table_body,
                id={"type": TABLE_TYPE_TABLE, "id": TABLE_NSIP_EXPORT_ID},
                bordered=True,
                hover=True,
            ),
        ]
    )


def nsip_build_user_declarations(declarations, agent_email, data_columns):
    """
    Build the list of html.Tr corresponding to the various projects af a given user.

    :param declarations: declarations dataframe
    :param agent_email: user RESEDA email
    :param data_columns: name of columns to add in each row
    :return: list of Tr
    """

    user_declarations = declarations[declarations.email_auth == agent_email]
    tr_list = [
        # rowSpan must be len+1 because the first row attached to the email is in a separate Tr
        # (rowSpan is in fact the number of Tr following this one attached to it)
        html.Tr(
            [
                (
                    html.Td(
                        [
                            dbc.Checkbox(
                                id={"type": "nsip-export-user", "id": agent_email},
                                class_name="nsip-agent-selector",
                                value=False,
                            ),
                            dcc.Store(
                                id={"type": "nsip-export-user-selected", "id": agent_email},
                                data=0,
                            ),
                        ],
                        className="align-middle ",
                        rowSpan=len(user_declarations) + 1,
                    )
                    if user_declarations["selectable"].any()
                    else html.Td(rowSpan=len(user_declarations) + 1)
                ),
                nsip_build_poject_declaration_cell(user_declarations, "email_auth", None),
                dcc.Store(
                    id={"type": "nsip-selected-user", "id": agent_email},
                    data=agent_email,
                ),
            ]
        )
    ]

    tr_list.extend(
        [
            html.Tr([nsip_build_poject_declaration_cell(row, c, i) for c in data_columns])
            for i, row in declarations[declarations.email_auth == agent_email].iterrows()
        ]
    )

    return tr_list


def nsip_build_poject_declaration_cell(declaration, column, row_index):
    """
    Build the column cell for one project declaration. Returns a html.Td.

    :param declaration: project declaration row or rows if column='email_auth'
    :param column: column name
    :param row_index: row index in the dataframe: must be a unique id for the row. Ignored if
                      declaration is a dataframe.
    :return: html.Td hor html.Th if column='email_auth'
    """

    if column == "email_auth":
        div_id = f"export-row-{declaration.iloc[0]['row_index']}-{column}"
        cell_content = [html.Div(declaration.iloc[0]["email_auth"], id=div_id)]
    else:
        div_id = f"export-row-{row_index}-{column}"
        cell_content = [html.Div(declaration[column], id=div_id)]
    cell_opt_class, tooltip = project_declaration_class(declaration, column)
    if tooltip:
        cell_content.append(dbc.Tooltip(tooltip, target=div_id))

    if column == "email_auth":
        return html.Th(
            cell_content,
            className=f"align-middle {cell_opt_class}",
            rowSpan=len(declaration) + 1,
        )
    else:
        return html.Td(cell_content, className=f"align-middle {cell_opt_class}")


def project_declaration_class(declaration, column):
    """
    Return the appropriate CSS class for each project declaration cell based on declaration
    attributes

    :param declaration: declaration row or rows if column='email_auth'
    :param column: column for which CSS must be configured (allow to distingish between time and
                   time unit)
    :return: CSS class names to add, tooltip text
    """

    global_params = GlobalParams()

    if column == "time_unit":
        if declaration["time_unit_mismatch"]:
            return (
                "table-warning",
                f"Unité incorrecte, requiert : {declaration['volume']}",
            )
    elif column == "time":
        if declaration["declaration_ok"]:
            return "table-success", None
        elif declaration["ositah_missing"]:
            # Flag only the declaration time for missing declarations in OSITAH
            return (
                "table-danger",
                "Declaration trouvée dans NSIP mais absente ou non-validée dans OSITAH",
            )
        elif declaration["invalid_time"]:
            return (
                "table-danger",
                (
                    f"Le temps déclaré pour ce type de projet ne peut pas dépasser"
                    f" {global_params.declaration_options['max_hours']} heures"
                ),
            )
        elif declaration["nsip_inconsistency"]:
            # CSS class nsip_inconsistency is returned for time column only if there is a
            # time mismatch
            return (
                "table-warning",
                (
                    f"Le temps déclaré dans OSITAH est différent de celui de NSIP"
                    f" ({int(declaration['time_nsipd'])})"
                ),
            )
    elif column == "validation_time":
        if declaration["mgr_val_time_mismatch"]:
            return (
                "table-warning",
                (
                    f"La date de validation est différente de celle de NSIP"
                    f" ({declaration['managerValidationDate']})"
                ),
            )
    elif column in ["nsip_master", "nsip_project"]:
        if math.isnan(declaration["nsip_project_id"]) and math.isnan(
            declaration["nsip_reference_id"]
        ):
            return (
                "table-danger",
                "Pas de projet correspondant dans NSIP: vérifier le referentiel Hito",
            )
    elif column == "email_auth":
        fullname_txt = f"Nom: {declaration.loc[declaration.index[0], 'fullname']}"
        if declaration["declaration_ok"].all():
            return "table-success", fullname_txt
        elif declaration["nsip_agent_missing"].any():
            if declaration["optional"].all():
                return "table-info", [
                    html.Div(fullname_txt),
                    html.Div(
                        (
                            f"Agent dont la déclaration est optionnelle non présent dans NSIP"
                            f" ({declaration.loc[declaration.index[0], 'statut']})"
                        )
                    ),
                ]
            else:
                return "table-warning", [
                    html.Div(fullname_txt),
                    html.Div("Agent non trouvé dans NSIP"),
                ]
        elif declaration["ositah_missing"].all():
            # Set the cell class to table-danger on the agent email only if all declarations for the
            # agent are missing
            return "table-danger", [
                html.Div(fullname_txt),
                html.Div("Toutes les déclarations sont manquantes ou non validées dans OSITAH"),
            ]
        else:
            return "", fullname_txt

    return "", None


def add_nsip_declaration_selection_switch(current_set):
    """
    Add a dbc.RadioItems to select whether to show all declaration or only the not
    synchronized ones in NSIP export table.

    :param current_set: currently selected declaration set
    :return: dbc.RadioItems
    """

    return dbc.Row(
        [
            dbc.RadioItems(
                options=[
                    {
                        "label": "Toutes les déclarations",
                        "value": NSIP_DECLARATIONS_SELECT_ALL,
                    },
                    {
                        "label": "Déclarations non synchronisées uniquement",
                        "value": NSIP_DECLARATIONS_SELECT_UNSYNCHRONIZED,
                    },
                ],
                value=current_set,
                id=NSIP_DECLARATIONS_SWITCH_ID,
                inline=True,
            ),
        ],
        justify="center",
    )


@app.callback(
    [
        Output(TAB_ID_EXPORT_NSIP, "children"),
        Output(EXPORT_SAVED_LOAD_INDICATOR_ID, "data"),
        Output(EXPORT_SAVED_ACTIVE_TAB_ID, "data"),
    ],
    [
        Input(EXPORT_LOAD_INDICATOR_ID, "data"),
        Input(EXPORT_TAB_MENU_ID, "active_tab"),
        Input(TEAM_SELECTED_VALUE_ID, "data"),
        Input(DATA_SELECTED_SOURCE_ID, "data"),
        Input(NSIP_DECLARATIONS_SELECTED_ID, "data"),
    ],
    [
        State(TEAM_SELECTION_DATE_ID, "data"),
        State(EXPORT_SAVED_LOAD_INDICATOR_ID, "data"),
        State(VALIDATION_PERIOD_SELECTED_ID, "data"),
        State(EXPORT_SAVED_ACTIVE_TAB_ID, "data"),
    ],
    prevent_initial_call=True,
)
def display_export_table(
    load_in_progress,
    active_tab,
    team,
    data_source,
    declaration_set,
    team_selection_date,
    previous_load_in_progress,
    period_date: str,
    previous_active_tab,
):
    """
    Display active tab contents after a team or an active tab change.

    :param load_in_progress: load in progress indicator
    :param tab: tab name
    :param team: selected team
    :param data_source: Hito (non-validated declarations) or OSITAH (validated declarations)
    :param declaration_set: declarations subset selected
    :param team_selection_date: last time the team selection was changed
    :param previous_load_in_progress: previous value of the load_in_progress indicator
    :param period_date: a date that must be inside the declaration period
    :param previous_active_tab: previously active tab
    :return: tab content
    """

    tab_contents = []

    # Be sure to fill the return values in the same order as Output are declared
    tab_list = [TAB_ID_EXPORT_NSIP]
    for tab in tab_list:
        if team and len(team) > 0 and tab == active_tab:
            if load_in_progress > previous_load_in_progress and active_tab == previous_active_tab:
                if active_tab == TAB_ID_EXPORT_NSIP:
                    tab_contents.append(
                        nsip_export_table(team, team_selection_date, period_date, declaration_set)
                    )
                else:
                    tab_contents.append(
                        dbc.Alert("Erreur interne: tab non supporté"), color="warning"
                    )
                previous_load_in_progress += 1
            else:
                component = html.Div(
                    [
                        create_progress_bar(team, duration=EXPORT_PROGRESS_BAR_MAX_DURATION),
                        dcc.Interval(
                            id=EXPORT_LOAD_TRIGGER_INTERVAL_ID,
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
    Output(EXPORT_LOAD_INDICATOR_ID, "data"),
    Input(EXPORT_LOAD_TRIGGER_INTERVAL_ID, "n_intervals"),
    State(EXPORT_SAVED_LOAD_INDICATOR_ID, "data"),
    prevent_initial_call=True,
)
def export_tables_trigger(n, previous_load_indicator):
    """
    Increment (change) input of display_export_table callback to get it fired a
    second time after displaying the progress bar. The output component must be updated each
    time the callback is entered to trigger the execution of the other callback, thus the
    choice of incrementing it at each call.

    :param n: n_interval property of the dcc.Interval (0 or 1)
    :return: 1 increment to previous value
    """

    return previous_load_indicator + 1


@app.callback(
    Output({"type": "nsip-export-user-selected", "id": MATCH}, "data"),
    Input({"type": "nsip-export-user", "id": MATCH}, "value"),
    State({"type": "nsip-selected-user", "id": MATCH}, "data"),
    prevent_initial_call=True,
)
def nsip_export_select_user(state, agent_email):
    """
    Mark the user as selected for NSIP export.

    :param state: checkbox state
    :param agent_email: RESEDA email of the selected user
    :return:
    """

    global_params = GlobalParams()
    try:
        session_data = global_params.session_data
    except SessionDataMissing:
        return no_session_id_jumbotron()
    declarations = session_data.nsip_declarations

    if state:
        declarations.loc[declarations.email_auth == agent_email, "selected"] = True
    else:
        declarations.loc[declarations.email_auth == agent_email, "selected"] = False

    return state


@app.callback(
    Output(NSIP_EXPORT_ALL_SELECTED_ID, "data"),
    Input(NSIP_EXPORT_SELECT_ALL_ID, "value"),
    prevent_initial_call=True,
)
def nsip_export_select_all_agents(checked):
    """
    Mark all selectable agents as selected if checked=1 or unselect all otherwise

    :param checked: checkbox value
    :return: checkbox value
    """

    global_params = GlobalParams()
    try:
        session_data = global_params.session_data
    except SessionDataMissing:
        return no_session_id_jumbotron()
    declarations = session_data.nsip_declarations

    declarations.loc[declarations.selectable, "selected"] = checked

    return checked


# A client-side callback is used to update the selection indicator (checkbox) of all rows after
# clicking the "Select all" button
app.clientside_callback(
    """
    function define_checkbox_status(checked) {
        const checkbox_forms = document.querySelectorAll(".nsip-agent-selector");
        checkbox_forms.forEach(function(cb_form) {
            const agent = cb_form.querySelector("input");
            /*console.log("Updating checkbox for "+agent.id);*/
            if ( checked ) {
                agent.checked = true;
            } else {
                agent.checked = false;
            }
        });
        return checked;
    }
    """,
    Output(NSIP_EXPORT_SELECTION_STATUS_ID, "data"),
    Input(NSIP_EXPORT_ALL_SELECTED_ID, "data"),
    prevent_initial_call=True,
)


@app.callback(
    Output(NSIP_EXPORT_BUTTON_ID, "children"),
    Output(NSIP_EXPORT_BUTTON_ID, "title"),
    Output(NSIP_EXPORT_BUTTON_ID, "disabled"),
    Input({"type": "nsip-export-user-selected", "id": ALL}, "data"),
    Input(NSIP_EXPORT_ALL_SELECTED_ID, "data"),
    prevent_initial_call=True,
)
def nsip_export_selected_count(*_):
    """
    Callback updating the export button label with the number of selected agent, each time a
    selection is changed. The button is also disabled if no agent is selected. Cannot be merged
    with nsip_export_select_user callback as MATCH and non MATCH output cannot be mixed.

    :param *_: input values are ignored
    :return: label of the export button
    """

    global_params = GlobalParams()
    try:
        session_data = global_params.session_data
    except SessionDataMissing:
        return no_session_id_jumbotron()
    declarations = session_data.nsip_declarations

    selected_users = declarations[declarations.selected].email_auth.unique()
    if len(selected_users):
        selected_count = f" ({len(selected_users)})"
    else:
        selected_count = ""

    return (
        f"{NSIP_EXPORT_BUTTON_LABEL}{selected_count}",
        (
            f"{len(selected_users)} agent{'s' if len(selected_users) > 1 else ''}"
            f" sélectionné{'s' if len(selected_users) > 1 else ''}"
        ),
        False if len(selected_users) else True,
    )


@app.callback(
    [
        Output(NSIP_EXPORT_STATUS_ID, "children"),
        Output(NSIP_EXPORT_STATUS_ID, "is_open"),
        Output(NSIP_EXPORT_STATUS_ID, "color"),
        Output(EXPORT_NSIP_SAVED_SYNC_INDICATOR_ID, "data"),
    ],
    [
        Input(NSIP_EXPORT_BUTTON_ID, "n_clicks"),
        Input(EXPORT_NSIP_SYNC_INDICATOR_ID, "data"),
    ],
    [
        State(EXPORT_NSIP_SAVED_SYNC_INDICATOR_ID, "data"),
        State(VALIDATION_PERIOD_SELECTED_ID, "data"),
    ],
    prevent_initial_call=True,
)
def nsip_export_button(n_clicks, sync_indicator, previous_sync_indicator, period_date):
    """
    Push into NSIP declarations for all the selected users. All project declarations for the user
    are added/updated. This callback is entered twice: the first time it displays a progress
    bar and start a dcc.Interval, the second time it does the real synchronisation work.

    :param n_clicks: checkbox state
    :param sync_indicator: current value of sync indicator
    :param previous_sync_indicator: previous value of sync indicator
    :return: agent/project updates failed
    """

    global_params = GlobalParams()
    try:
        session_data = global_params.session_data
    except SessionDataMissing:
        return no_session_id_jumbotron()
    declarations = session_data.nsip_declarations
    selected_declarations = declarations[declarations.selectable & declarations.selected]
    start_date, _ = get_validation_period_dates(period_date)
    failed_updates = []
    failed_exports = 0
    successful_exports = 0

    if n_clicks and n_clicks >= 1:
        if sync_indicator > previous_sync_indicator:
            for row in selected_declarations.itertuples(index=False):
                # One of the possible error during declaration update is that the user has
                # multiple contracts attached to the lab for the current period. In this case
                # the update is retried with the second contract (generally the current one)
                # mentioned in the error message.
                retry_on_error = True
                retry_attempts = 0
                contract = None
                while retry_on_error:
                    # nsip_project_id and nsip_reference_id are NaN if undefined and a NaN value is
                    # not equal to itself!
                    project_type = row.nsip_project_id == row.nsip_project_id
                    activity_id = row.nsip_project_id if project_type else row.nsip_reference_id
                    (
                        status,
                        http_status,
                        http_reason,
                    ) = global_params.nsip.update_declaration(
                        row.email_reseda,
                        activity_id,
                        project_type,
                        row.time,
                        start_date,
                        row.validation_time,
                        contract,
                    )

                    if status > 0 and http_reason:
                        m = EXPORT_NSIP_MULTIPLE_CONTRACTS_ERROR.match(http_reason)
                        # Never retry more than once
                        if m and (retry_attempts == 0):
                            contract = m.group("id2")
                            retry_attempts += 1
                            print(
                                (
                                    f"Agent {row.email_reseda} has several contracts for the"
                                    f" current period: retrying update with contract {contract}"
                                )
                            )
                        else:
                            retry_on_error = False
                    else:
                        retry_on_error = False

                if status <= 0:
                    # Log a message if the declaration was successfully added to NSIP to make
                    # diagnostics easier. After a successful addition or update, http_status
                    # contains the declaration ID instead of the http status
                    if status == 0:
                        action = "added to"
                    else:
                        action = "updated in"
                    print(
                        (
                            f"Declaration {http_status} for user {row.email_auth} (NSIP ID:"
                            f" {row.email_reseda}), {'project' if project_type else 'reference'}"
                            f" ID={int(activity_id)}, master={row.nsip_master}, name="
                            f"{row.nsip_project} {action} NSIP"
                        ),
                        flush=True,
                    )
                    successful_exports += 1

                else:
                    if http_status:
                        http_error = f" (http status={http_status}, reason={http_reason})"
                    else:
                        http_error = ""
                    print(
                        (
                            f"ERROR: update of declaration failed for user {row.email_auth}"
                            f" (NSIP ID: {row.email_reseda}),"
                            f" {'project' if project_type else 'reference'} ID="
                            f"{int(activity_id)}, master={row.nsip_master}, name="
                            f"{row.nsip_project}{http_error}"
                        ),
                        flush=True,
                    )
                    failed_exports += 1
                    # Limit the number of explicit failed update displayed to avoid a too long
                    # message
                    if failed_exports < EXPORT_MAX_FAILDED_UPDATES:
                        failed_updates.append(
                            f"{row.email_auth}:{row.nsip_master}/{row.nsip_project}"
                        )
                    elif failed_exports == EXPORT_MAX_FAILDED_UPDATES:
                        failed_updates.append("...")

                previous_sync_indicator += 1
        else:
            component = html.Div(
                [
                    create_progress_bar(
                        duration=(len(selected_declarations) / EXPORT_NSIP_SYNC_FREQUENCY)
                    ),
                    dcc.Interval(
                        id=EXPORT_NSIP_SYNC_TRIGGER_INTERVAL_ID,
                        n_intervals=0,
                        max_intervals=1,
                        interval=500,
                    ),
                ]
            )
            return component, True, "success", previous_sync_indicator

    else:
        raise PreventUpdate

    if failed_exports == 0:
        update_status_msg = (
            f"Toutes les déclarations sélectionnées ({successful_exports})"
            f" ont été enregistrées dans NSIP"
        )
        color = "success"
    else:
        update_status_msg = [
            (
                f"{failed_exports} export{' a' if failed_exports == 1 else 's ont'} échoué :"
                f" {', '.join(failed_updates)}"
            ),
            html.Br(),
            (
                f"{successful_exports} déclaration"
                f"{' a' if successful_exports == 1 else 's ont'}"
                f" été synchronisée{'' if successful_exports == 1 else 's'}"
                f" avec succès"
            ),
        ]
        color = "warning"
    return update_status_msg, True, color, previous_sync_indicator


@app.callback(
    Output(EXPORT_NSIP_SYNC_INDICATOR_ID, "data"),
    Input(EXPORT_NSIP_SYNC_TRIGGER_INTERVAL_ID, "n_intervals"),
    State(EXPORT_NSIP_SAVED_SYNC_INDICATOR_ID, "data"),
    prevent_initial_call=True,
)
def nsip_export_button_trigger(n, previous_load_indicator):
    """
    Increment (change) input of nsip_export_button callback to get it fired a
    second time after displaying the progress bar. The output component must be updated each
    time the callback is entered to trigger the execution of the other callback, thus the
    choice of incrementing it at each call.

    :param n: n_interval property of the dcc.Interval (0 or 1)
    :return: 1 increment to previous value
    """

    return previous_load_indicator + 1


@app.callback(
    Output(NSIP_DECLARATIONS_SELECTED_ID, "data"),
    Input(NSIP_DECLARATIONS_SWITCH_ID, "value"),
    prevent_initial_call=True,
)
def select_declarations_set(new_set):
    """
    This callback is used to forward to the NSIP export callback the selected declarations set
    through a dcc.Store that exists permanently in the page.

    :param new_set: selected declarations set
    :return: same value
    """

    return new_set

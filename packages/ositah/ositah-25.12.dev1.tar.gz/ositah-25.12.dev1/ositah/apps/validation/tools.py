"""
Various functions used by Validation sub-application
"""

from datetime import date, datetime

import dash_bootstrap_components as dbc
import pandas as pd
from dash import html

from ositah.apps.validation.parameters import (
    VALIDATION_DECLARATIONS_SELECT_ALL,
    VALIDATION_DECLARATIONS_SELECT_NOT_VALIDATED,
    VALIDATION_DECLARATIONS_SELECT_VALIDATED,
    VALIDATION_DECLARATIONS_SWITCH_ID,
)
from ositah.utils.exceptions import SessionDataMissing
from ositah.utils.hito_db import get_db
from ositah.utils.period import get_validation_period_data
from ositah.utils.projects import (
    CATEGORY_DEFAULT,
    DATA_SOURCE_HITO,
    get_team_projects,
    project_time,
    time_unit,
)
from ositah.utils.utils import (
    SEMESTER_HOURS,
    TIME_UNIT_HOURS,
    TIME_UNIT_HOURS_EN,
    TIME_UNIT_WEEKS,
    WEEK_HOURS,
    GlobalParams,
    no_session_id_jumbotron,
)


def activity_time_cell(row, column, row_index):
    """
    Build the cell content for an activity time, adding the appropriate class and in case of
    inconsistencies between the Hito declared time and the validated time, add a tooltip
    to display both values.

    :param row: declaration row
    :param column: column name for the cell to build
    :param row_index: row index of the current row
    :return: html.Td
    """

    global_params = GlobalParams()

    classes = "text-center align-middle"
    cell_value = int(round(row[column]))
    cell_id = f"validation-table-value-{row_index}-{column}"

    if column == "percent_global":
        thresholds = global_params.declaration_options["thresholds"]["current"]
        percent = round(row["percent_global"], 1)
        if percent <= thresholds["low"]:
            percent_class = "table-danger"
            tooltip_txt = f"Percentage low (<={thresholds['low']}%)"
        elif percent <= thresholds["suspect"]:
            percent_class = "table-warning"
            tooltip_txt = (
                f"Percentage suspect (>{thresholds['low']}% and" f" <={thresholds['suspect']}%)"
            )
        elif percent > thresholds["good"]:
            percent_class = "table-info"
            tooltip_txt = f"Percentage too high (>{thresholds['good']}%)"
        else:
            percent_class = "table-success"

        contents = [html.Div(percent, id=cell_id)]
        if percent_class != "table-success":
            contents.append(dbc.Tooltip(html.Div(tooltip_txt), target=cell_id))

        classes += f" {percent_class}"

    elif (
        (column != "enseignement" or not global_params.teaching_ratio)
        and time_unit(column) == TIME_UNIT_HOURS_EN
        and row[column] > global_params.declaration_options["max_hours"]
    ):
        contents = [
            html.Div(cell_value, id=cell_id),
            dbc.Tooltip(
                html.Div(
                    (
                        f"Déclaration supérieure au maximum"
                        f" ({global_params.declaration_options['max_hours']} heures)"
                    )
                ),
                target=cell_id,
            ),
        ]
        classes += " table-danger"

    elif row.hito_missing:
        validated_column = f"{column}_val"
        contents = [
            html.Div(int(round(row[validated_column])), id=cell_id),
            dbc.Tooltip(
                [
                    html.Div(f"Déclaration validée: {round(row[validated_column], 3)}"),
                    html.Div("Déclaration Hito correspondante supprimée"),
                ],
                target=cell_id,
            ),
        ]
        classes += " validated_hito_missing"

    elif row.validated and not row[f"{column}_time_ok"]:
        validated_column = f"{column}_val"
        contents = [
            html.Div(cell_value, id=cell_id),
            dbc.Tooltip(
                [
                    html.Div(f"Dernière déclaration: {round(row[column], 3)}"),
                    html.Div(f"Déclaration validée: {round(row[validated_column], 3)}"),
                ],
                target=cell_id,
            ),
        ]
        classes += " table-warning"

    else:
        contents = [html.Div(cell_value, id=cell_id)]
        if row.suspect:
            contents.append(
                dbc.Tooltip(
                    [
                        html.Div("Déclaration suspecte: vérifier les quotités déclarées"),
                    ],
                    target=cell_id,
                )
            )
            classes += " table-warning"

    return html.Td(contents, className=classes, key=f"validation-table-cell-{row}-{column}")


def agent_tooltip_txt(agent_data, data_columns):
    """
    Build the tooltip text associated with an agent.

    :param agent_data: the dataframe row corresponding to the agent
    :param data_columns: the list of columns to use to compute the total time
    :return: list of html elements
    """

    global_params = GlobalParams()

    if agent_data["hito_missing"]:
        tooltip_detail = "Déclarations validées supprimées de Hito"
    else:
        tooltip_detail = f"Total (semaines) : {total_time(agent_data, data_columns)}"
    tooltip_txt = [
        html.Div(
            f"{global_params.column_titles['team']}: {agent_data[global_params.columns['team']]}"
        ),
        html.Div(tooltip_detail),
    ]

    return tooltip_txt


def add_validation_declaration_selection_switch(current_set):
    """
    Add a dbc.RadioItems to select whether to show all declaration or only a subset.

    :param current_set: currently selected declaration set
    :return: dbc.RadioItems
    """

    return dbc.Row(
        [
            dbc.RadioItems(
                options=[
                    {
                        "label": "Toutes les déclarations",
                        "value": VALIDATION_DECLARATIONS_SELECT_ALL,
                    },
                    {
                        "label": "Déclarations non validées uniquement",
                        "value": VALIDATION_DECLARATIONS_SELECT_NOT_VALIDATED,
                    },
                    {
                        "label": "Déclarations validées uniquement",
                        "value": VALIDATION_DECLARATIONS_SELECT_VALIDATED,
                    },
                ],
                value=current_set,
                id=VALIDATION_DECLARATIONS_SWITCH_ID,
                inline=True,
            ),
        ],
        justify="center",
    )


def agent_list(dataframe: pd.DataFrame) -> pd.DataFrame:
    global_params = GlobalParams()
    fullname_df = pd.DataFrame()
    fullname_df[global_params.columns["fullname"]] = dataframe[
        global_params.columns["fullname"]
    ].drop_duplicates()
    return fullname_df


def total_time(row, categories, rounded=True) -> int:
    """
    Compute total time declared by an agent in weeks

    :param row: dataframe row for an agent
    :param categories: list of categories to sum up
    :param rounded: if true, returns the rounded value
    :return: number of weeks declared
    """

    global_params = GlobalParams()

    weeks_number = 0
    hours_number = 0
    for category in categories:
        if global_params.time_unit[category] == TIME_UNIT_WEEKS:
            weeks_number += row[category]
        elif global_params.time_unit[category] == TIME_UNIT_HOURS:
            hours_number += row[category]
        else:
            raise Exception(
                (
                    f"Unsupported time unit '{global_params.time_unit[category]}'"
                    f" for category {category}"
                )
            )

    weeks_number += hours_number / WEEK_HOURS

    if rounded:
        return int(round(weeks_number))
    else:
        return weeks_number


def category_time(dataframe, category) -> None:
    """
    Convert the number of hours into the time unit of the category. Keep track of the
    conversions done to prevent doing it twice.

    :param dataframe: dataframe to update
    :param category: category name
    :return: none, dataframe updated
    """

    global_params = GlobalParams()

    # Default time unit is hour
    unit_hour = True
    if category in global_params.time_unit:
        if global_params.time_unit[category] == TIME_UNIT_WEEKS:
            unit_hour = False
        elif global_params.time_unit[category] != TIME_UNIT_HOURS:
            raise Exception(
                (
                    f"Unsupported time unit '{global_params.time_unit[category]}'"
                    f" for category {category}"
                )
            )

    if not unit_hour:
        dataframe[category] = dataframe[category] / WEEK_HOURS

    return


def agent_project_time(agent: str) -> html.Div:
    """
    Return a HTML Div with the list of projects and the time spent on them

    :param agent: agent fullname
    :return: html.Div
    """

    global_params = GlobalParams()
    columns = global_params.columns

    try:
        session_data = global_params.session_data
        df = session_data.project_declarations[
            session_data.project_declarations[global_params.columns["fullname"]] == agent
        ]

        return html.Div(
            [
                html.P(
                    (
                        f"{df.iloc[i][global_params.columns['activity']]}:"
                        f" {' '.join(project_time(df.iloc[i][columns['activity']], df.iloc[i][columns['hours']]))}"  # noqa: E501
                    )
                )
                for i in range(len(df))
            ]
        )

    except SessionDataMissing:
        return no_session_id_jumbotron()


def category_declarations(
    project_declarations: pd.DataFrame, use_cache: bool = True
) -> pd.DataFrame:
    """
    Process the project declarations (time per project) and convert it into declarations by
    category of projects.

    :param project_declarations: project declarations to consolidate
    :param use_cache: if True, use and update cache
    :return: dataframe
    """

    global_params = GlobalParams()
    columns = global_params.columns

    try:
        session_data = global_params.session_data
    except SessionDataMissing:
        return no_session_id_jumbotron()

    # Check if there is a cached version
    if session_data.category_declarations is not None and use_cache:
        return session_data.category_declarations

    if project_declarations is not None:
        category_declarations = project_declarations.copy()
        categories = [CATEGORY_DEFAULT]
        categories.extend(global_params.project_categories.keys())
        for category in categories:
            category_declarations[category] = category_declarations.loc[
                category_declarations[columns["category"]] == category, columns["hours"]
            ]
        category_declarations.drop(columns=columns["hours"], inplace=True)
        category_declarations.fillna(0, inplace=True)
        category_declarations = category_declarations.infer_objects(copy=False)

        agg_functions = {c: "sum" for c in categories}
        agg_functions["suspect"] = "any"
        category_declarations_pt = pd.pivot_table(
            category_declarations,
            index=[
                global_params.columns["fullname"],
                global_params.columns["team"],
                global_params.columns["agent_id"],
            ],
            values=[*categories, "suspect"],
            aggfunc=agg_functions,
        )
        category_declarations = pd.DataFrame(category_declarations_pt.to_records())

        category_declarations["total_hours"] = category_declarations[categories].sum(axis=1)
        category_declarations["percent_global"] = (
            category_declarations["total_hours"] / SEMESTER_HOURS * 100
        )

        # Convert category time into the appropriate unit
        for column_name in categories:
            category_time(category_declarations, column_name)

    else:
        raise Exception("Project declarations are not defined")

    if use_cache:
        session_data.category_declarations = category_declarations

    return category_declarations


def define_declaration_thresholds(period_date: str):
    """
    Define the declaration thresholds (low, suspect, normal) for the current period

    :param period_date: a date that must be inside the declaration period
    """
    global_params = GlobalParams()

    period_datetime = date.fromisoformat(period_date)
    if period_datetime.month >= 7:
        global_params.declaration_options["thresholds"]["current"] = (
            global_params.declaration_options["thresholds"]["s2"]
        )
    else:
        global_params.declaration_options["thresholds"]["current"] = (
            global_params.declaration_options["thresholds"]["s1"]
        )


def get_validation_data(agent_id, period_date: str, session=None):
    """
    Return the validation data for an agent or None if there is no entry in the database for this
    agent_id.

    :param agent_id: agent_id of the agent to check
    :param session: DB session to use (default one if None)
    :param period_date: a date that must be inside the declaration period
    :return: an OSITAHValidation object or None
    """
    from ositah.utils.hito_db_model import OSITAHValidation

    db = get_db()
    if session is None:
        session = db.session

    validation_period = get_validation_period_data(period_date)
    return (
        session.query(OSITAHValidation)
        .filter_by(agent_id=agent_id, period_id=validation_period.id)
        .order_by(OSITAHValidation.timestamp.desc())
        .first()
    )


def get_validation_status(agent_id, period_date: str, session=None):
    """
    Return True if the agent entry has been validated, False otherwise (including if there is no
    validation entry for the agent)

    :param agent_id:  agent_id of the agent to check
    :param session: DB session to use
    :param period_date: a date that must be inside the declaration period
    :return: boolean
    """

    validation_data = get_validation_data(agent_id, period_date, session)
    if validation_data is None:
        return False
    else:
        return validation_data.validated


def get_all_validation_status(period_date: str):
    """
    Returns the list of agents whose declaration has been validated as a dataframe. It is intended
    to be used to build the validation table but should not be used when updating the status, as
    it may have been updated by somebody else.

    :param period_date: a date that must be inside the declaration period
    :return: dataframe
    """

    from ositah.utils.hito_db_model import OSITAHValidation

    db = get_db()
    validation_period = get_validation_period_data(period_date)
    # By design, only one entry in the declaration period can be with the status validated,
    # except if the database has been messed up...
    validation_query = OSITAHValidation.query.filter(
        OSITAHValidation.period_id == validation_period.id,
        OSITAHValidation.validated,
    )
    validation_data = pd.read_sql(validation_query.statement, con=db.engine)
    if validation_data is None:
        validation_data = pd.DataFrame()
    else:
        validation_data.set_index("agent_id", inplace=True)

    return validation_data


def validation_started(period_date: str):
    """
    Compare the current date with the validation start date (validation_date) and return True
    if the validation has started, False otherwise.

    :param period_date: date included in the declaration period
    :return: boolean
    """

    current_date = datetime.now()
    period_params = get_validation_period_data(period_date)
    if current_date >= period_params.validation_date:
        return True
    else:
        return False


def project_declaration_snapshot(
    agent_id,
    validation_id,
    team,
    team_selection_date,
    period_date,
    db_session=None,
    commit=False,
):
    """
    Save into table ositah_validation_project_declaration the validated project declarations
    for an agent.

    :param agent_id: agent (ID) whose project declarations must be saved
    :param validation_id: validation ID associated with the declarations snapshot
    :param db_session: session for the current transaction. If None, use the default one.
    :param commit: if false, do not commit added rows
    :return: None
    """

    from ositah.utils.hito_db_model import OSITAHProjectDeclaration

    global_params = GlobalParams()
    columns = global_params.columns
    try:
        session_data = global_params.session_data
    except SessionDataMissing:
        return no_session_id_jumbotron()

    db = get_db()
    if db_session:
        session = db_session
    else:
        session = db.session

    # The cache cannot be used directly as the callback may run on a server where the session
    # cache for the current user doesn't exist yet
    project_declarations = get_team_projects(
        team, team_selection_date, period_date, DATA_SOURCE_HITO
    )
    agent_projects = project_declarations[project_declarations[columns["agent_id"]] == agent_id]
    if agent_projects is None:
        print(f"ERROR: no declaration found for agent ID '{agent_id}' (internal error)")
    else:
        for _, project in agent_projects.iterrows():
            declaration = OSITAHProjectDeclaration(
                projet=project[columns["project"]],
                masterprojet=project[columns["masterproject"]],
                category=project[columns["category"]],
                hours=project[columns["hours"]],
                quotite=project[columns["quotite"]],
                validation_id=validation_id,
                hito_project_id=project[columns["activity_id"]],
            )
            try:
                session.add(declaration)
            except Exception:
                # If the default session is used, let the caller process the exception and
                # eventually do the rollback
                if db_session:
                    session.rollback()
                raise

        # Reset the cache of validated declarations if a modification occured
        session_data.reset_validated_declarations_cache()

        if commit:
            session.commit

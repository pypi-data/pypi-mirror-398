# Helper functions related to projects and time declarations

import re
from datetime import datetime
from typing import List, Tuple

import numpy as np
import pandas as pd
from sqlalchemy.orm import joinedload

from ositah.utils.agents import get_agents
from ositah.utils.cache import clear_cached_data
from ositah.utils.exceptions import InvalidDataSource, InvalidHitoProjectName
from ositah.utils.hito_db import get_db
from ositah.utils.period import get_validation_period_data
from ositah.utils.utils import (
    DAY_HOURS,
    TEAM_LIST_ALL_AGENTS,
    TIME_UNIT_HOURS,
    TIME_UNIT_HOURS_EN,
    TIME_UNIT_HOURS_FR,
    TIME_UNIT_WEEKS,
    TIME_UNIT_WEEKS_EN,
    TIME_UNIT_WEEKS_FR,
    WEEK_HOURS,
    GlobalParams,
)

CATEGORY_DEFAULT = "nsip_project"

DATA_SOURCE_HITO = "hito"
DATA_SOURCE_OSITAH = "ositah"

NSIP_CLASS_OTHER_ACTIVITY = "activitensipreferentiel"
NSIP_CLASS_PROJECT = "projetnsipreferentiel"

MASTERPROJECT_DELETED_ACTIVITY = "Disabled"
MASTERPROJECT_LOCAL_PROJECT = "Local Projects"

NSIP_PROJECT_ORDER = 1
LOCAL_PROJECT_ORDER = 2
NSIP_ACIVITY_ORDER = 3
DISABLED_ACTIVITY_ORDER = 9999


def hito2ositah_project_name(hito_name):
    """
    Split a Hito project name into a masterprojet and project name

    :param hito_name: Hito name with  masterprojet and project name separated by a /
    :return: masterprojet and project name
    """
    masterproject, project_name = hito_name.split(" / ", 2)
    return masterproject, project_name


def ositah2hito_project_name(masterproject, project):
    """
    Build the Hito/NSIP project name from the masterproject and project

    :param masterproject: masterproject name
    :param project: project name
    :return: Hito/NSIP project fullname
    """
    return " / ".join([masterproject, project])


def nsip2ositah_project_name(masterproject, project):
    """
    Build the OSITAH project name from the NSIP project name, removing the master project
    name if it is at the head of the NSIP project name, except if the master project name
    and the project name are identical.

    :param masterproject: masterproject name
    :param project: project name
    :return: OSITAH project name (without the masterproject name)
    """

    if project != masterproject:
        m = re.match(rf"{masterproject}\s+\-\s+(?P<project>.*)", project)
        if m:
            project = m.group("project")

    return project


def category_from_activity(category_patterns, activity) -> str:
    """
    Return the activity category if the activity matches the pattern. Else an empty string.
    Called as a lambda to build the category column.

    :param category_patterns: category patterns to match against the activity (dict where
                              the key is the pattern and the value is the category)
    :param activity: activity name
    :return: category or np.Nan
    """

    for pattern, category in category_patterns.items():
        if re.match(pattern.lower(), activity.lower()):
            return category

    return np.NaN


def activity_from_project(project):
    """
    Return the activity the project belongs to.

    :param project: project name
    :return: activity name
    """

    global_params = GlobalParams()

    for activity, pattern in global_params.project_categories.items():
        if re.match(pattern, project):
            return activity

    return CATEGORY_DEFAULT


def reference_masterproject(reference_type):
    """
    Return an OSITAH masterproject for a NSIP reference, based on its type.
    Masterprojects for each type is defined in the configuration. A reference type
    without a match or with an empty value is ignored (np.NaN returned).

    :param reference_type: NSIP reference type
    :return: matching master project
    """

    global_params = GlobalParams()

    for type_pattern, masterproject in global_params.reference_masterprojects.items():
        if re.match(type_pattern.lower(), reference_type.lower()):
            if len(masterproject) > 0:
                return masterproject
            else:
                return np.NaN

    return np.NaN


def time_unit(category, short=False, english=True, parenthesis=False) -> str:
    """
    Return the time unit as defined in the configuration as a string. If the category/column is
    not in the configuration, return an empty string.

    :param category: project category/class
    :param short: if true, return abbreviated unit names
    :param english: return english unit names if true. Also implies short=False
    :param parenthesis: if True, enclose the string in ()
    :return: time unit for the category as a string
    """

    global_params = GlobalParams()

    if english:
        unit_w = TIME_UNIT_WEEKS_EN
        unit_h = TIME_UNIT_HOURS_EN
    else:
        if short:
            unit_w = "sem."
            unit_h = "h"
        else:
            unit_w = TIME_UNIT_WEEKS_FR
            unit_h = TIME_UNIT_HOURS_FR

    if category in global_params.time_unit:
        if global_params.time_unit[category] == TIME_UNIT_WEEKS:
            unit_str = unit_w
        elif global_params.time_unit[category] == TIME_UNIT_HOURS:
            unit_str = unit_h
        else:
            raise Exception(
                (
                    f"Unsupported time unit '{global_params.time_unit[category]}'"
                    f" for category {category}"
                )
            )
    else:
        return ""

    if parenthesis:
        return f"({unit_str})"
    else:
        return unit_str


def category_time_and_unit(category, hours, short=True, english=False) -> Tuple[int, str]:
    """
    Return the rounded category time in the appropriate unit and the category time unit

    :param category: project category/class
    :param hours: number of hours
    :param short: if true, return abbreviated unit names
    :param english: return english unit names if true. Also implies short=False
    :return: project time, project unit
    """

    global_params = GlobalParams()

    unit = time_unit(category, short, english)

    if global_params.time_unit[category] == "w":
        declared_time = f"{int(round(hours / WEEK_HOURS))}"
    else:
        declared_time = f"{int(round(hours))}"

    return declared_time, unit


def project_time(project, hours):
    """
    Return the rounded project time in the appropriate unit and the project time unit

    :param project: project name
    :param hours: number of hours
    :return: project time, abbreviated project unit
    """

    return category_time_and_unit(activity_from_project(project), hours)


def get_team_projects(
    team,
    team_selection_date,
    period_date: datetime,
    source=DATA_SOURCE_HITO,
    use_cache: bool = True,
):
    """
    Query the Hito database and return a dataframe will all the project contributions for a given
    team. The dataframe has one row for each each agent contribution to each project.

    :param team: selected team or TEAM_LIST_ALL_AGENTS for all teams
    :param team_selection_date: last time the team selection was changed
    :param period_date: a date that must be inside the declaration period
    :param source: whether to use Hito (non validated) or OSITAH (validated) as a data source
    :param use_cache: if true, use the cache if defined and up-to-date or update it with the
                      new declarations
    :return: dataframe or None if the query returned no entry
    """

    from ositah.utils.hito_db_model import (
        ActiviteDetail,
        Agent,
        OSITAHProjectDeclaration,
        OSITAHValidation,
        Projet,
        Team,
    )

    global_params = GlobalParams()
    columns = global_params.columns
    session_data = global_params.session_data
    db = get_db()

    validation_period = get_validation_period_data(period_date)

    # Check if there is a cached version
    if session_data.project_declarations is not None and use_cache:
        if (
            session_data.project_declarations_source is None
            or source != session_data.project_declarations_source
            or datetime.fromisoformat(team_selection_date) > session_data.cache_date
        ):
            # Cache must be refreshed if the selected source doesn't match the cached one or if
            # the team has been modified since the cache was loaded (required for multi-worker
            # configurations as the team selection does not necessarily happen on the same worker
            # than the later processing). In a multi-worker configuration is used it may also
            # happen that the declaration source is not defined if it was initially initialised
            # on another worker
            clear_cached_data()
        else:
            return session_data.project_declarations

    if source == DATA_SOURCE_OSITAH:
        # The query relies on the fact that only one validation entry can be in the validated
        # state for a given period, something enforced by the declaration validation.
        # When a team is specified, display all projects from this team and the children teams
        query = (
            OSITAHProjectDeclaration.query.join(
                OSITAHValidation,
                OSITAHProjectDeclaration.validation_id == OSITAHValidation.id,
            )
            .join(Agent, Agent.id == OSITAHValidation.agent_id)
            .join(Team, Team.id == Agent.team_id)
            .add_entity(Agent)
            .add_entity(Team)
            .add_entity(OSITAHValidation)
            .filter(OSITAHValidation.validated)
            .filter(OSITAHValidation.period_id == validation_period.id)
        )
        if team != TEAM_LIST_ALL_AGENTS:
            query = query.filter(Team.nom.ilike(f"{team}%"))
        declarations = pd.read_sql(query.statement, db.session.bind)
        if len(declarations) == 0:
            return None
        declarations.rename(columns={"id": columns["activity_id"]}, inplace=True)
        declarations.rename(columns={"id_1": columns["agent_id"]}, inplace=True)
        declarations.rename(columns={"nom_1": columns["team"]}, inplace=True)
        declarations.rename(columns={"hours": columns["hours"]}, inplace=True)
        declarations.rename(columns={"id_3": "validation_id"}, inplace=True)
        declarations.rename(columns={"timestamp": "validation_time"}, inplace=True)
        # Drop statut column to avoid conflicts in future merge with the Agent table
        declarations.drop(columns=["statut"], inplace=True)
        # Ensure that email_auth is defined and if it is not, replace it by the email.
        declarations.loc[declarations[columns["email_auth"]].isna(), columns["email_auth"]] = (
            declarations[columns["email"]]
        )
        declarations[columns["activity"]] = declarations.apply(
            lambda row: ositah2hito_project_name(
                row[columns["masterproject"]], row[columns["project"]]
            ),
            axis=1,
        )

    elif source == DATA_SOURCE_HITO:
        # For team names, we want to keep the agent team name instead of the team_name in
        # activity_details so it must be specified explicitely in the join with Team table
        query = (
            ActiviteDetail.query.join(Projet)
            .join(Agent)
            .join(Team, Team.id == Agent.team_id)
            .add_entity(Projet)
            .add_entity(Agent)
            .add_entity(Team)
            .filter(
                ActiviteDetail.date >= validation_period.start_date,
                ActiviteDetail.date <= validation_period.end_date,
            )
        )
        if team != TEAM_LIST_ALL_AGENTS:
            query = query.filter(Team.nom.ilike(f"{team}%"))
        daily_declarations = pd.read_sql(query.statement, db.session.bind)
        if len(daily_declarations) == 0:
            return None
        # Pandas add a suffix to duplicate column names, the first one being unchanged, the
        # second being suffixed _1...
        daily_declarations.drop(columns=["id", "id_1", "id_2"], inplace=True)
        daily_declarations.rename(columns={"agent_id": columns["agent_id"]}, inplace=True)
        daily_declarations.rename(columns={"libelle": columns["activity"]}, inplace=True)
        daily_declarations.rename(columns={"nom_1": columns["team"]}, inplace=True)
        for column in [columns["hours"], columns["percent"]]:
            daily_declarations[column] = daily_declarations[column].astype(float)
        # Ensure that email_auth is defined and if it is not, replace it by the email. If left
        # undefined, the entries will not be present in the pivot table as it is part of the index.
        daily_declarations.loc[
            daily_declarations[columns["email_auth"]].isna(), columns["email_auth"]
        ] = daily_declarations[columns["email"]]
        # Rebuild agent quotite by comparing the time declared with the percent computed by Hito
        # based on the quotite
        daily_declarations[columns["quotite"]] = (
            daily_declarations[columns["hours"]] / DAY_HOURS * 100
        ) / daily_declarations[columns["percent"]]
        global_declarations_pt = pd.pivot_table(
            daily_declarations,
            index=[
                columns["lastname"],
                columns["firstname"],
                columns["activity"],
                columns["activity_id"],
                columns["team"],
                columns["agent_id"],
                columns["email_auth"],
                columns["email"],
            ],
            values=[columns["hours"], columns["quotite"]],
            aggfunc={columns["hours"]: "sum", columns["quotite"]: "mean"},
        )
        declarations = pd.DataFrame(global_declarations_pt.to_records())
        declarations[[columns["masterproject"], columns["project"]]] = declarations[
            columns["activity"]
        ].str.split(" / ", n=1, expand=True)
        # An entry in the pseudo master project MASTERPROJECT_DELETED_ACTIVITY is a special
        # case corresponding to deleted NSIP projects: the real name is in the project part that
        # must be parsed as for any other project
        declarations["project_saved"] = np.NaN
        declarations["project_saved"] = declarations["project_saved"].astype("object")
        declarations.loc[
            declarations[columns["masterproject"]] == MASTERPROJECT_DELETED_ACTIVITY,
            "project_saved",
        ] = declarations[columns["project"]]
        # Not sure why the following line doesn't work (masterproject and project set to NaN
        # if no row matches the indexing condition... An issue has been open:
        # https://github.com/pandas-dev/pandas/issues/44726.
        # declarations.loc[
        #     declarations.project_saved.notna(),
        #     [columns["masterproject"], columns["project"]],
        # ] = declarations.project_saved.str.split(" / ", n=1, expand=True)
        #
        # The following workaround fails if project_saved contains only np.NaN. It is a known
        # issue in Panda 1.3.4, see https://github.com/pandas-dev/pandas/issues/35807
        # declarations[
        #     ["newmaster", "newproject"]
        # ] = declarations.project_saved.str.split(" / ", n=1, expand=True)
        #
        # Workaround based on
        # https://github.com/pandas-dev/pandas/issues/35807#issuecomment-676912441. If no row
        # matches the condition, only one column is created thus the need to check they all
        # exist.
        tmp_columns = ["newmaster", "newproject"]
        saved_projects = (
            declarations["project_saved"]
            .str.split("/", expand=True, n=len(tmp_columns) - 1)
            .rename(columns={k: name for k, name in enumerate(tmp_columns)})
        )
        for column in tmp_columns:
            if column not in saved_projects.columns:
                saved_projects[column] = np.NaN
        declarations = declarations.join(saved_projects)
        declarations.loc[declarations.project_saved.notna(), columns["masterproject"]] = (
            declarations.newmaster
        )
        declarations.loc[declarations.project_saved.notna(), columns["project"]] = (
            declarations.newproject
        )
        declarations.drop(columns=["newmaster", "newproject"], inplace=True)
        declarations.loc[declarations.project_saved.notna(), columns["activity"]] = (
            declarations.project_saved
        )

        # Detect project names not matching the format "masterproject / project"
        invalid_hito_projects = declarations.loc[declarations[columns["project"]].isnull()]
        if not invalid_hito_projects.empty:
            raise InvalidHitoProjectName(
                pd.Series(invalid_hito_projects[columns["masterproject"]]).unique()
            )

    else:
        raise InvalidDataSource(source)

    declarations[columns["fullname"]] = declarations[
        [columns["lastname"], columns["firstname"]]
    ].agg(" ".join, axis=1)
    declarations[columns["category"]] = declarations.apply(
        lambda row: category_from_activity(
            global_params.category_patterns, row[columns["activity"]]
        ),
        axis=1,
    )
    declarations.loc[declarations[columns["category"]].isna(), "category"] = CATEGORY_DEFAULT

    # Check quotite < 50% and flag the entry as suspect (generally means confusion between quotite
    # and percent during declaration)
    declarations["suspect"] = declarations[columns["quotite"]] < 0.5

    if use_cache:
        session_data.set_project_declarations(declarations, source)

    return declarations


def get_all_hito_activities(project_activity: bool):
    """
    Retrieve all projects or all activities defined in Hito with their associated teams

    :param project_activity: if true, return all projects, else all Hito activities
    :return: dataframe
    """

    from ositah.utils.hito_db_model import Activite, Projet

    global_params = GlobalParams()
    session_data = global_params.session_data
    db = get_db()

    # Check if there is a cached version
    if session_data.get_hito_activities(project_activity) is not None:
        return session_data.get_hito_activities(project_activity)

    else:
        if project_activity:
            Activity = Projet
        else:
            Activity = Activite

        query = Activity.query.options(joinedload(Activity.teams))
        activities = pd.read_sql(query.statement, db.session.bind)
        activities[["masterproject", "project"]] = activities.libelle.str.split(
            " / ", n=1, expand=True
        )
        activities.rename(columns={"description_1": "team_description"}, inplace=True)
        activities.rename(columns={"nom": "team_name"}, inplace=True)

        session_data.set_hito_activities(activities, project_activity)

        return activities


def build_projects_data(team, team_selection_date, period_date: str, source):
    """
    Build the project list contributed by the selected team and return it as a dataframe

    :param team: selected team
    :param team_selection_date: last time the team selection was changed
    :param period_date: a date that must be inside the declaration period
    :param source: whether to use Hito (non validated) or OSITAH (validated) as a data source
    :return: dataframe with projects data, dataframe with agent declarations
    """

    global_params = GlobalParams()
    columns = global_params.columns
    session_data = global_params.session_data

    declaration_list = get_team_projects(team, team_selection_date, period_date, source)
    if declaration_list is None:
        return None, None

    projects_data = session_data.projects_data
    if projects_data is None:
        projects_data_pt = pd.pivot_table(
            declaration_list,
            index=[
                columns["masterproject"],
                columns["project"],
                columns["activity"],
                columns["category"],
            ],
            values=[columns["hours"]],
            aggfunc={columns["hours"]: "sum"},
        )
        projects_data = pd.DataFrame(projects_data_pt.to_records())
        projects_data[columns["hours"]] = np.round(projects_data[columns["hours"]]).astype("int")
        projects_data[columns["weeks"]] = np.round(projects_data[columns["hours"]] / WEEK_HOURS, 1)
        short_name_len = 25
        projects_data["project_short"] = projects_data[columns["project"]]
        projects_data.loc[
            projects_data["project_short"].str.len() > short_name_len, "project_short"
        ] = projects_data["project_short"].str.slice_replace(start=short_name_len - 4, repl="...")
        session_data.projects_data = projects_data

    return projects_data, declaration_list


def get_hito_nsip_activities(project_activity: bool = True):
    """
    Return a dataframe with all the NSIP activities defined in Hito. Activities can be
    either projects or "references" (other activities). An activity is considered as a
    NSIP activity if it has a matching entry in Hito referentiel.

    :param project_activity: if true, return projects, else references
    :return: dataframe
    """

    from ositah.utils.hito_db_model import Projet, Referentiel

    db = get_db()

    if project_activity:
        project_join_id = Projet.projet_nsip_referentiel_id
        referentiel_class = "projetnsipreferentiel"
    else:
        project_join_id = Projet.activite_nsip_referentiel_id
        referentiel_class = "activitensipreferentiel"

    activity_query = (
        Projet.query.join(Referentiel, Referentiel.id == project_join_id)
        .add_entity(Referentiel)
        .filter(
            Referentiel.object_class == referentiel_class,
        )
    )

    activities = pd.read_sql(activity_query.statement, db.session.bind)

    activities.drop(
        columns=[
            "ordre",
            "projet_nsip_referentiel_id",
            "activite_nsip_referentiel_id",
        ],
        inplace=True,
    )
    activities.rename(columns={"id_1": "referentiel_id"}, inplace=True)
    activities.rename(columns={"libelle_1": "nsip_name_id"}, inplace=True)

    if activities.empty:
        activities[["nsip_master", "nsip_project", "nsip_project_id", "nsip_reference_id"]] = [
            np.NaN,
            np.NaN,
            np.NaN,
            np.NaN,
        ]
    else:
        activities[["nsip_master", "nsip_project", "nsip_project_id", "nsip_reference_id"]] = (
            activities.apply(
                lambda v: nsip_activity_name_id(v["nsip_name_id"], v["class"]),
                axis=1,
                result_type="expand",
            )
        )
        activities["nsip_project_id"] = activities["nsip_project_id"].astype(int)
        activities["nsip_reference_id"] = activities["nsip_reference_id"].astype(int)

    return activities


def get_hito_projects():
    """
    Return a dataframe with the information about all projects with validated declarations
    in the current declaration period defined in Hito and their relationship to NSIP, if relevant.

    :return: Hito project dataframe
    """

    from ositah.utils.hito_db_model import (
        OSITAHProjectDeclaration,
        OSITAHValidation,
        Projet,
        Referentiel,
    )

    db = get_db()

    projects_query = (
        Projet.query.join(Referentiel, Referentiel.id == Projet.projet_nsip_referentiel_id)
        .join(OSITAHProjectDeclaration)
        .join(OSITAHValidation)
        .add_entity(Referentiel)
        .add_entity(OSITAHValidation)
        .filter(
            Referentiel.object_class == "projetnsipreferentiel",
            OSITAHValidation.validated,
        )
    )
    projects = pd.read_sql(projects_query.statement, db.session.bind)

    activities_query = (
        Projet.query.join(Referentiel, Referentiel.id == Projet.activite_nsip_referentiel_id)
        .join(OSITAHProjectDeclaration)
        .join(OSITAHValidation)
        .add_entity(Referentiel)
        .add_entity(OSITAHValidation)
        .filter(
            Referentiel.object_class == "activitensipreferentiel",
            OSITAHValidation.validated,
        )
    )
    activities = pd.read_sql(activities_query.statement, db.session.bind)

    projects_activities = pd.concat([projects, activities], ignore_index=True)

    projects_activities.drop(
        columns=[
            "id_2",
            "ordre",
            "projet_nsip_referentiel_id",
            "activite_nsip_referentiel_id",
            "agent_id",
        ],
        inplace=True,
    )
    projects_activities.rename(columns={"id_1": "referentiel_id"}, inplace=True)
    projects_activities.rename(columns={"libelle_1": "nsip_name_id"}, inplace=True)
    projects_activities.drop_duplicates(subset=["id"], inplace=True)

    if projects_activities.empty:
        projects_activities[
            ["nsip_master", "nsip_project", "nsip_project_id", "nsip_reference_id"]
        ] = [np.NaN, np.NaN, np.NaN, np.NaN]
    else:
        projects_activities[
            ["nsip_master", "nsip_project", "nsip_project_id", "nsip_reference_id"]
        ] = projects_activities.apply(
            lambda v: nsip_activity_name_id(v["nsip_name_id"], v["class"]),
            axis=1,
            result_type="expand",
        )
        projects_activities["nsip_project_id"] = projects_activities["nsip_project_id"].astype(int)
        projects_activities["nsip_reference_id"] = projects_activities["nsip_reference_id"].astype(
            int
        )

    return projects_activities


def nsip_activity_name_id(hito_name: str, type: str) -> List[str]:
    """
    Split the NISP activity project name in Hito referentiel in 3 parts: masterproject name,
    project name, project ID and return the project ID as the project ID (3d value) or reference
    ID (4th value) depending on the activity type. The unused ID is set to 0 rather than np.NaN
    or pd.NA as the column may be used in merges.

    :param hito_name: activity name in Hito referentiel
    :param type: referentiel class
    :return:
    """

    m = re.match(
        r"(?P<master>.*?)\s+/\s+(?P<project>.*)\s+\(NSIP ID:\s*(?P<id>\w+)\)$",
        hito_name,
    )
    if m:
        try:
            _ = int(m.group("id"))
        except ValueError:
            print(
                (
                    f"ERROR: invalid NSIP ID in Hito referentiel for '{m.group('master')} /"
                    f" {m.group('project')}' (ID={m.group('id')})"
                )
            )
            return m.group("master"), m.group("project"), 0, 0
        if type == NSIP_CLASS_PROJECT:
            project_id = m.group("id")
            reference_id = 0
        else:
            project_id = 0
            reference_id = m.group("id")
        return m.group("master"), m.group("project"), project_id, reference_id
    else:
        print(
            (
                f"ERROR: invalid Hito referentiel entry format, cannot be parsed as"
                f" master/project/id ({hito_name})"
            )
        )
        return np.NaN, np.NaN, 0, 0


def get_nsip_declarations(period_date: str, team: str):
    """
    Return the NSIP declaration list for the declaration period matching a given date (the
    date must be included in the period) as a dataframe

    :param period_date: date that must be inside the period
    :param team: selected team
    :return: declaration list as a dataframe
    """

    global_params = GlobalParams()

    if global_params.nsip:
        declarations = pd.json_normalize(global_params.nsip.get_declarations(period_date))
        if declarations.empty:
            return declarations

        declarations.rename(columns={"id": "id_declaration"}, inplace=True)
        # Set NaN to 0 in reference as np.NaN is a float and prevent casting to int. As it will
        # be used in a merge better to have a 0 than a NaN.
        if "project.id" in declarations.columns:
            declarations.loc[declarations["project.id"].isna(), "project.id"] = 0
            declarations["project.id"] = declarations["project.id"].astype(int)
        else:
            declarations["project.id"] = 0
            declarations["project.name"] = np.NaN
        if "reference.id" in declarations.columns:
            declarations.loc[declarations["reference.id"].isna(), "reference.id"] = 0
            declarations["reference.id"] = declarations["reference.id"].astype(int)
        else:
            declarations["reference.id"] = 0
        declarations["nsip_fullname"] = (
            declarations["agent.lastname"] + " " + declarations["agent.firstname"]
        )

        if team != TEAM_LIST_ALL_AGENTS:
            team_agents = get_agents(period_date, team)
            agent_emails = team_agents["email_auth"]
            declarations = declarations.merge(
                agent_emails,
                how="inner",
                left_on="agent.email",
                right_on="email_auth",
                suffixes=[None, "_agent"],
            )

        return declarations

    else:
        return None


def get_nsip_activities(project_activity: bool):
    """
    Retrieve laboratory activities defined in NSIP and return them in a dataframe.
    Activities can be either projects or references (other activities).

    :param project_activity: true for projects, false for other activities
    :return: dataframe or None if NSIP is not configured
    """

    global_params = GlobalParams()

    if global_params.nsip:
        activities = pd.json_normalize(
            global_params.nsip.get_activities(project_activity), record_prefix=True
        )
        if not activities.empty:
            if project_activity:
                activities["ositah_name"] = activities.apply(
                    lambda p: nsip2ositah_project_name(p["master_project.name"], p["name"]),
                    axis=1,
                )
            else:
                activities["master_project.name"] = activities.apply(
                    lambda p: reference_masterproject(p["type"]),
                    axis=1,
                )
                activities.drop(
                    activities[activities["master_project.name"].isna()].index,
                    inplace=True,
                )
                activities["ositah_name"] = activities["name"]

        return activities
    else:
        return None


def build_activity_libelle(
    nsip_id: str,
    master_project: str,
    project: str,
):
    """
    Build Hito project name and referentiel entry name from NSIP master project, project name and
    project id.

    :param nsip_id: NSIP ID for the project
    :param master_project: master project name
    :param project: project name
    :return: Hito project name, Hito referentiel name
    """

    new_project_name = f"{master_project} / {project}"
    new_referentiel_name = f"{new_project_name} (NSIP ID: {nsip_id})"
    return new_project_name, new_referentiel_name


def update_activity_name(
    hito_project_id: str,
    hito_referentiel_id: str,
    nsip_id: str,
    master_project: str,
    project: str,
):
    """
    Update a project name in Hito, both in the referentiel and in the project/activity table.

    :param hito_project_id: Hito project ID
    :param hito_referentiel_id: Hito referentiel ID for the project
    :param nsip_id: NSIP ID for the project
    :param master_project: master project name
    :param project: project name
    :return: 0 if update succeeded, non-zero if an error occured, error_msg if
             an error occured
    """

    from ositah.utils.hito_db_model import Projet, Referentiel

    db = get_db()

    status = 0  # Assume success
    error_msg = ""
    new_project_name, new_referentiel_name = build_activity_libelle(
        nsip_id,
        master_project,
        project,
    )

    try:
        referentiel_entry = Referentiel.query.filter(Referentiel.id == hito_referentiel_id).first()
        project_entry = Projet.query.filter(Projet.id == hito_project_id).first()
        referentiel_entry.libelle = new_referentiel_name
        project_entry.libelle = new_project_name
        change_log_msg = f"Modifié le {datetime.now()}"
        if project_entry.description:
            project_entry.description += f"; {change_log_msg}"
        else:
            project_entry.description = change_log_msg
        db.session.commit()
    except Exception as e:
        status = 1
        error_msg = getattr(e, "message", repr(e))
        db.session.rollback()

    return status, error_msg


def add_activity(
    nsip_id: str,
    master_project: str,
    project: str,
    activity_teams: List[str],
    project_activity: bool,
):
    """
    Adds a new project in Hito referenciel and in Hito project/activity table

    :param nsip_id: NSIP ID for the project
    :param master_project: master project name
    :param project: project name
    :param activity_teams: list of team IDs associated with the project
    :param project_activity: if True it is a NSIP project, else a NSIP activity
    :return: 0 if update succeeded, non-zero if an error occured, error_msg if
             an error occured
    """

    from ositah.utils.hito_db_model import Projet, Referentiel, Team

    db = get_db()

    status = 0  # Assume success
    error_msg = ""
    project_name, referentiel_name = build_activity_libelle(
        nsip_id,
        master_project,
        project,
    )

    if project_activity:
        entry_class = "projetnsipreferentiel"
        entry_order = NSIP_PROJECT_ORDER
    else:
        entry_class = "activitensipreferentiel"
        entry_order = NSIP_ACIVITY_ORDER

    try:
        referentiel_entry = Referentiel(
            libelle=referentiel_name,
            object_class=entry_class,
            ordre=entry_order,
        )
        activity_entry = Projet(
            libelle=project_name,
            description=f"Créé le {datetime.now()}",
            ordre=entry_order,
        )
        if activity_teams:
            activity_entry.teams = Team.query.filter(Team.id.in_(activity_teams)).all()
        db.session.add(referentiel_entry)
        db.session.add(activity_entry)
        db.session.commit()
        # Define relationship between activity and referentiel entry after creating them so that
        # the referentiel ID generated by the DB server can be accessed
        if project_activity:
            activity_entry.projet_nsip_referentiel_id = referentiel_entry.id
        else:
            activity_entry.activite_nsip_referentiel_id = referentiel_entry.id
        db.session.commit()

    except Exception as e:
        status = 1
        error_msg = getattr(e, "message", repr(e))
        db.session.rollback()

    return status, error_msg


def remove_activity(
    hito_project_id: str,
    hito_referentiel_id: str,
    nsip_id: str,
    project_activity: bool,
):
    """
    Remove the association between a Hito activity (project or reference) and NSIP. The Hito
    activity is kept as it may be referenced by other objects but its description is updated
    to mention that it is no longer in NSIP. The project name is updated so that it appears in the
    pseudo-masterproject NSIP_DELETED_MASTERPROJECT. Associated teams are removed.

    :param hito_project_id: Hito project ID
    :param hito_referentiel_id: Hito referentiel ID for the project
    :param nsip_id: NSIP ID for the project
    :param project_activity: if True it is a NSIP project, else a NSIP activity
    :return: 0 if update succeeded, non-zero if an error occured, error_msg if
             an error occured
    """

    from ositah.utils.hito_db_model import Projet, Referentiel

    db = get_db()

    status = 0  # Assume success
    error_msg = ""

    try:
        referentiel_entry = Referentiel.query.filter(Referentiel.id == hito_referentiel_id).first()
        db.session.query()
        activity_entry = Projet.query.filter(Projet.id == hito_project_id).first()
        if project_activity:
            activity_entry.projet_nsip_referentiel_id = None
        else:
            activity_entry.activite_nsip_referentiel_id = None
        change_log_msg = f"Desactivé le {datetime.now()} (NSIP ID={nsip_id})"
        if activity_entry.description:
            activity_entry.description += f"; {change_log_msg}"
        else:
            activity_entry.description = change_log_msg
        activity_entry.libelle = f"{MASTERPROJECT_DELETED_ACTIVITY} / {activity_entry.libelle}"
        activity_entry.ordre = DISABLED_ACTIVITY_ORDER
        if len(activity_entry.teams) > 0:
            activity_entry.teams.clear()
        db.session.delete(referentiel_entry)
        db.session.commit()
    except Exception as e:
        status = 1
        error_msg = getattr(e, "message", repr(e))
        db.session.rollback()

    return status, error_msg


def add_activity_teams(
    masterproject: str, project: str, team_list: List[str], project_activity: bool
):
    """
    Add teams to an activity.

    :param masterproject: activity masterproject name
    :param project: activity project name
    :param team_list: list of team names to add
    :param project_activity: if true, an Hito project else an Hito activity
    :return: status (0 if success), error_msg (empty if success)
    """

    from ositah.utils.hito_db_model import Activite, Projet, Team

    db = get_db()

    status = 0  # Assume success
    error_msg = ""

    if project_activity:
        Activity = Projet
    else:
        Activity = Activite

    activity_name = ositah2hito_project_name(masterproject, project)
    activity = Activity.query.filter(Activity.libelle == activity_name).first()

    if activity:
        try:
            for team in team_list:
                team_object = Team.query.filter(Team.nom == team).first()
                activity.teams.append(team_object)
            db.session.commit()
        except Exception as e:
            status = 1
            error_msg = getattr(e, "message", repr(e))
            db.session.rollback()

    return status, error_msg


def remove_activity_teams(
    masterproject: str, project: str, team_list: List[str], project_activity: bool
):
    """
    Remove teams from an activity. If the team is not present in teams list, silently
    ignore it.

    :param masterproject: activity masterproject name
    :param project: activity project name
    :param team_list: list of team names to remove
    :param project_activity: if true, an Hito project else an Hito activity
    :return: status (0 if success), error_msg (empty if success)
    """

    from ositah.utils.hito_db_model import Activite, Projet, Team

    db = get_db()

    status = 0  # Assume success
    error_msg = ""

    if project_activity:
        Activity = Projet
    else:
        Activity = Activite

    activity_name = ositah2hito_project_name(masterproject, project)
    activity = Activity.query.filter(Activity.libelle == activity_name).first()

    if activity:
        try:
            for team in team_list:
                team_object = Team.query.filter(Team.nom == team).first()
                if team_object in activity.teams:
                    activity.teams.remove(team_object)
            db.session.commit()
        except Exception as e:
            status = 1
            error_msg = getattr(e, "message", repr(e))
            db.session.rollback()

    return status, error_msg


def reenable_activity(activity_name: str, project_activity: bool, name_prefix: str = None):
    """
    Reenable a disabled activity. This involves:
    - Updating master project to match the original one
    - If it was an NSIP project, recreate the referentiel entry

    :param activity_name: activity name
    :param project_activity: if true, an Hito project else an Hito activity
    :param name_prefix: activity name prefix for deleted or local activities
    :return: status and error message if any
    """

    from ositah.utils.hito_db_model import Activite, Projet, Referentiel

    db = get_db()

    status = 0  # Assume success
    error_msg = ""

    if project_activity:
        Activity = Projet
    else:
        Activity = Activite

    # Retrieve activity attributes and NSIP ID if present in description
    if name_prefix:
        activity_full_name = f"{name_prefix} / {activity_name}"
    else:
        activity_full_name = activity_name
    activity_entry = Activity.query.filter(Activity.libelle == activity_full_name).first()

    m = re.search(r"\(NSIP ID\=(?P<id>\d+)\)$", activity_entry.description)
    if m:
        nsip_id = m.group("id")
    else:
        nsip_id = None

    # Check if an entry exist in the referentiel for the NSIP ID: if not, create it
    nsip_entry = Referentiel.query.filter(
        Referentiel.libelle.ilike(f"%(NSIP ID = {nsip_id})")
    ).first()
    if not nsip_entry:
        master_project, activity = hito2ositah_project_name(activity_name)
        project_name, referentiel_name = build_activity_libelle(
            nsip_id,
            master_project,
            activity,
        )

        if project_activity:
            entry_class = "projetnsipreferentiel"
            entry_order = NSIP_PROJECT_ORDER
        else:
            entry_class = "activitensipreferentiel"
            entry_order = NSIP_ACIVITY_ORDER

        referentiel_entry = Referentiel(
            libelle=referentiel_name,
            object_class=entry_class,
            ordre=entry_order,
        )
    else:
        referentiel_entry = None

    # Create referentiel entry if necessary and update activity
    try:
        if referentiel_entry:
            db.session.add(referentiel_entry)
        activity_entry.libelle = activity_name
        activity_entry.description = f"Modifié le {datetime.now()}"
        db.session.commit()
        # Define relationship between activity and referentiel entry after creating them so that
        # the referentiel ID generated by the DB server can be accessed
        if project_activity:
            activity_entry.projet_nsip_referentiel_id = referentiel_entry.id
        else:
            activity_entry.activite_nsip_referentiel_id = referentiel_entry.id
        db.session.commit()

    except Exception as e:
        status = 1
        error_msg = getattr(e, "message", repr(e))
        db.session.rollback()

    # Clear cached data to force a refresh of project list
    clear_cached_data()

    return status, error_msg

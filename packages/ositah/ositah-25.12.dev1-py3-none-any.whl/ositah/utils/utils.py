# Convenience objects for OSITAH application

from datetime import datetime, timedelta
from typing import List

import dash_bootstrap_components as dbc
from dash import html
from flask import session
from flask_sqlalchemy import SQLAlchemy
from hito_tools.exceptions import ConfigFileEmpty, ConfigMissingParam
from hito_tools.nsip import nsip_session_init
from hito_tools.utils import load_config_file

from ositah.app import app

from .core import singleton
from .exceptions import SessionDataMissing

CONFIG_DEFAULT_PORT = "8888"

# Define the dataframe column name to use for each kind of information
# The key is the kind of information, the value is the column name and must be lowercase
COLUMN_NAMES = {
    "agent_id": "id",
    "activity": "project_fullname",
    "activity_id": "projet_id",
    "category": "category",
    "cem": "cem",
    "declarations_number": "declarations_number",
    "email": "email",
    "email_auth": "email_auth",
    "firstname": "prenom",
    "fullname": "fullname",
    "hours": "nbHeures",
    "lastname": "nom",
    "masterproject": "masterprojet",
    "missings_number": "missings_number",
    "percent": "pourcent",
    "project": "projet",
    "quotite": "quotite",
    "statut": "statut",
    "team": "team",
    "team_id": "team_id",
    "weeks": "weeks",
}

# Define the column names in the NSIP export and the matching column name in the validated
# declarations dataframe
NSIP_COLUMN_NAMES = {
    "email_auth": "reseda_eamil",
    "nsip_project_id": "projet_id",
    "nsip_reference_id": "reference_id",
    "nsip_master": "masterprojet",
    "nsip_project": "projet",
    "time": "time",
    "time_unit": "volume",
    "validation_time": "timestamp",
    "id_declaration": "NSIP declaration ID",
}

TIME_UNIT_HOURS = "h"
TIME_UNIT_HOURS_EN = "hours"
TIME_UNIT_HOURS_FR = "heures"
TIME_UNIT_WEEKS = "w"
TIME_UNIT_WEEKS_EN = "weeks"
TIME_UNIT_WEEKS_FR = "semaines"
TIME_UNIT_DEFAULT = TIME_UNIT_HOURS

# Hours per days and per week
DAY_HOURS = 7.7
WEEK_HOURS = 5 * DAY_HOURS
# Semester: assume no week of holidays
SEMESTER_WEEKS = 26
SEMESTER_HOURS = WEEK_HOURS * SEMESTER_WEEKS

TEAM_LIST_ALL_AGENTS = "Tous les agents"

HITO_ROLE_PROJECT_MGR = "ROLE_PROJECT_MANAGER"
HITO_ROLE_SUPER_ADMIN = "ROLE_SUPER_ADMIN"
HITO_ROLE_TEAM_MGR = "ROLE_RESP"
# Must be in role power reverse order
AUTHORIZED_ROLES = [HITO_ROLE_SUPER_ADMIN, HITO_ROLE_PROJECT_MGR, HITO_ROLE_TEAM_MGR]


class OSITAHSessionData:
    def __init__(self):
        self._cache_initialisation_date = None
        self._category_declarations = None
        self._project_declarations = None
        self._nsip_declarations = None
        self._projects_data = None
        self._project_declarations_source = None
        self._hito_activities = None
        self._hito_projects = None
        self._agent_list = None
        self._declaration_periods = None
        # Use a list for agent_teams to preserve the order
        self._agent_teams = []
        self._role = None

    @property
    def agent_teams(self):
        return self._agent_teams

    def add_teams(self, teams: List[str], sort_list=True) -> None:
        """
        Add a list of teams to agent_teams, without duplicates. The list is then sorted except
        is sort_list=False.

        :param teams: a list of team names
        :param sort: if true sort the resulting team list
        :return: None
        """
        seen = set(self.agent_teams)
        # Ensure that that there is no duplicate in the list
        self._agent_teams.extend([x for x in teams if not (x in seen or seen.add(x))])
        if sort_list:
            self._agent_teams.sort()

    @property
    def agent_list(self):
        return self._agent_list

    @agent_list.setter
    def agent_list(self, agent_list):
        self._agent_list = agent_list

    @property
    def cache_date(self):
        return self._cache_initialisation_date

    @property
    def category_declarations(self):
        return self._category_declarations

    @category_declarations.setter
    def category_declarations(self, declarations):
        self._category_declarations = declarations

    @property
    def declaration_periods(self):
        return self._declaration_periods

    @declaration_periods.setter
    def declaration_periods(self, periods):
        self._declaration_periods = periods

    def get_hito_activities(self, project_activity: bool):
        if project_activity:
            return self._hito_projects
        else:
            return self._hito_activities

    @property
    def nsip_declarations(self):
        return self._nsip_declarations

    @nsip_declarations.setter
    def nsip_declarations(self, declarations):
        self._nsip_declarations = declarations
        if self._cache_initialisation_date is None:
            # Define only if the cache has not yet been initialized
            self._cache_initialisation_date = datetime.now()

    @property
    def projects_data(self):
        return self._projects_data

    @projects_data.setter
    def projects_data(self, projects_data):
        self._projects_data = projects_data

    @property
    def project_declarations(self):
        return self._project_declarations

    @property
    def project_declarations_source(self):
        return self._project_declarations_source

    @property
    def role(self):
        return self._role

    @role.setter
    def role(self, role):
        self._role = role

    @property
    def total_declarations_num(self):
        return len(self._project_declarations)

    def reset_caches(self):
        self._category_declarations = None
        self._project_declarations = None
        self._nsip_declarations = None
        self._projects_data = None
        self._hito_activities = None
        self._hito_projects = None
        self._project_declarations_source = None
        self._cache_initialisation_date = None
        self._agent_list = None
        self._validation_data = None
        self._total_declarations_num = 0

    def reset_validated_declarations_cache(self):
        self._nsip_declarations = None

    def set_hito_activities(self, activities, project_activity: bool):
        if project_activity:
            self._hito_projects = activities
        else:
            self._hito_activities = activities

    def set_project_declarations(self, declarations, source):
        self._project_declarations = declarations
        self._project_declarations_source = source
        if self._cache_initialisation_date is None:
            # Define only if the cache has not yet been initialized
            self._cache_initialisation_date = datetime.now()


@singleton
class GlobalParams:
    def __init__(self):
        self.agent_query = None
        self.analysis_params = None
        self.category_patterns = {}
        self.columns = COLUMN_NAMES
        self.column_titles = None
        self.declaration_options = None
        self.project_categories = None
        self.reference_masterprojects = {}
        self.roles = {}
        self.time_unit = None
        self.ldap = None
        self.nsip = None
        self.project_teams = {}
        self.teaching_ratio = None
        self.port = CONFIG_DEFAULT_PORT
        self.validation_params = None
        self._hito_db = None
        self._session_data = {}

    @property
    def hito_db(self):
        if not self._hito_db:
            self._hito_db = SQLAlchemy(app.server)
        return self._hito_db

    @property
    def session_data(self):
        """
        Returns the session data for the current session. Must not be called if the session UID
        is not defined or will raise SessionDataMissing exception.

        :return: session data for the current session
        """

        if "uid" in session:
            # If 'uid' is defined, it means the user was successfully authenticated.
            if session["uid"] not in self._session_data:
                # session_data may not exist if a multi-worker configuration is used and the
                # authentication (done when moving from one subapp to another one) has been
                # done on another worker.
                self._session_data[session["uid"]] = OSITAHSessionData()
            return self._session_data[session["uid"]]

        else:
            raise SessionDataMissing()

    @session_data.deleter
    def session_data(self):
        if "uid" in session:
            if session["uid"] in self._session_data:
                del self._session_data[session["uid"]]
            else:
                print(
                    (
                        f"WARNING: attempt to delete non-existing session data for session"
                        f" {session['uid']} (user={session['user_id']})"
                    )
                )

        else:
            raise SessionDataMissing()


def define_config_params(file):
    """
    Validate configuration and define appropriate defaults. Also define global parameters
    from configuration.

    :param file: configuration file
    :return: updated configuration hash
    """

    global_params = GlobalParams()

    config = load_config_file(file, required=True)
    if not config:
        raise ConfigFileEmpty(file)

    if "server" not in config or not config["server"]:
        config["server"] = {}
    if "port" in config["server"]:
        global_params.port = config["server"]["port"]
    if "authentication" in config["server"]:
        if "ldap" in config["server"]["authentication"]:
            global_params.ldap = config["server"]["authentication"]["ldap"]
            for param in ["uri", "base_dn", "bind_dn", "password"]:
                if param not in global_params.ldap:
                    raise ConfigMissingParam(f"server/authentication/ldap/{param}", file)
        else:
            raise ConfigMissingParam("server/authentication/ldap", file)
        if "provider_name" not in config["server"]["authentication"]:
            raise ConfigMissingParam("server/authentication/provider_name", file)
    else:
        raise ConfigMissingParam("server/authentication", file)

    if "hito" not in config:
        raise ConfigMissingParam("hito", file)
    if "db" not in config["hito"]:
        raise ConfigMissingParam("hito/db", file)
    if "type" not in config["hito"]["db"]:
        raise ConfigMissingParam("hito/db/type", file)
    if "location" not in config["hito"]["db"]:
        raise ConfigMissingParam("hito/db/location", file)
    if "agent_query" not in config["hito"]["db"]:
        raise ConfigMissingParam("hito/db/agent_query", file)
    if config["hito"]["db"]["type"] == "sqlite":
        app.server.config["SQLALCHEMY_DATABASE_URI"] = (
            f"sqlite:///{config['hito']['db']['location']}"
        )
    elif config["hito"]["db"]["type"] == "mysql":
        if "user" not in config["hito"]["db"]:
            raise ConfigMissingParam("hito/db/user", file)
        if "password" not in config["hito"]["db"]:
            raise ConfigMissingParam("hito/db/passowrd", file)
        app.server.config["SQLALCHEMY_DATABASE_URI"] = (
            f"mysql+pymysql://{config['hito']['db']['user']}:{config['hito']['db']['password']}"
            f"@{config['hito']['db']['location']}"
        )
    else:
        raise Exception(f"Support for {config['hito']['db']['type']} not yet implemented...")
    if "inactivity_timeout" in config["hito"]["db"]:
        app.server.config["SQLALCHEMY_POOL_RECYCLE"] = config["hito"]["db"]["inactivity_timeout"]
    global_params.agent_query = contextualize_sql_query(
        config["hito"]["db"]["agent_query"], config["hito"]["db"]["type"]
    )
    app.server.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    if "categories" in config["hito"]:
        global_params.project_categories = config["hito"]["categories"]
        global_params.category_patterns = {
            v: k for k, v in global_params.project_categories.items()
        }
    else:
        raise ConfigMissingParam("hito/categories", file)

    if "time_unit" in config["hito"]:
        global_params.time_unit = config["hito"]["time_unit"]
    else:
        global_params.time_unit = {}
    for category in global_params.project_categories:
        if category not in global_params.time_unit:
            global_params.time_unit[category] = TIME_UNIT_DEFAULT

    if "titles" in config["hito"]:
        global_params.column_titles = config["hito"]["titles"]
    else:
        raise ConfigMissingParam("hito/titles", file)

    if "declaration" in config:
        if "optional_statutes" not in config["declaration"]:
            config["declaration"]["optional_statutes"] = []
        if "optional_teams" not in config["declaration"]:
            config["declaration"]["optional_teams"] = []
    else:
        config["declaration"] = {}
    if "max_hours" not in config["declaration"]:
        # Set a very high value
        config["declaration"]["max_hours"] = 99999
    missing_params = []
    for semester in ["s1", "s2"]:
        for k in ["low", "suspect", "good"]:
            if (
                "thresholds" not in config["declaration"]
                or semester not in config["declaration"]["thresholds"]
                or k not in config["declaration"]["thresholds"][semester]
            ):
                missing_params.append(f"declaration/thresholds/{semester}/{k}")
    if len(missing_params) > 0:
        raise ConfigMissingParam(", ".join(missing_params), file)
    # Default declaration period date defaults to current day if not explicitly defined
    if "default_date" not in config["declaration"]:
        if "period_change_delay" in config["declaration"]:
            change_delay = config["declaration"]["period_change_delay"]
        else:
            change_delay = 0
        config["declaration"]["default_date"] = datetime.now() - timedelta(days=change_delay)
    global_params.declaration_options = config["declaration"]

    if "analysis" not in config:
        config["analysis"] = {}
    if "contributions_sorted_by_name" not in config["analysis"]:
        config["analysis"]["contributions_sorted_by_name"] = True
    global_params.analysis_params = config["analysis"]

    if "validation" not in config:
        config["validation"] = {}
    if "override_period" not in config["validation"]:
        config["validation"]["override_period"] = []
    global_params.validation_params = config["validation"]

    if "roles" in config:
        global_params.roles = config["roles"]
    if "read-only" not in global_params.roles:
        global_params.roles["read-only"] = []

    if "project_teams" in config:
        global_params.project_teams = config["project_teams"]

    if "nsip" in config:
        global_params.nsip = nsip_session_init(config["nsip"])
        if "reference_masterprojects" in config["nsip"]:
            global_params.reference_masterprojects = config["nsip"]["reference_masterprojects"]
        if "teaching" in config["nsip"]:
            global_params.teaching_ratio = config["nsip"]["teaching"]
            if "ratio" not in global_params.teaching_ratio:
                raise ConfigMissingParam("nsip/teeaching/ratio", file)
            if "masterproject" not in global_params.teaching_ratio:
                global_params.teaching_ratio["masterproject"] = "Enseignement Supérieur"
            if "cem" not in global_params.teaching_ratio:
                global_params.teaching_ratio["cem"] = None

    return config


def contextualize_sql_query(query: str, db_type: str) -> str:
    """
    Function to replace placeholders in the query by the function/statement appropriate for
    the actual DB back-end used.

    :param query: the query with the placeholders
    :param db_type: the DB back-end type
    :return: the query for the selected back-end
    """

    if db_type == "sqlite":
        query = query.replace("$$TODAY$$", 'DATE("now")')
    elif db_type == "mysql":
        query = query.replace("$$TODAY$$", "CURRENT_DATE()")
        # pymysql uses the query string as a formatter string: % characters must be esacped
        query = query.replace("%", "%%")
    else:
        raise Exception(f"Support for {db_type} not yet implemented...")

    return query


def no_session_id_jumbotron(session_id=None):
    return html.Div([dbc.Jumbotron(html.P(["Internal error: session ID invalid or undefined"]))])


def general_error_jumbotron(error):
    """
    Print an error message that can be any representable object

    :param error: error object, e.g. an exception
    :return: a jumbotron
    """

    return html.Div([dbc.Jumbotron(html.P([repr(error)]))])

#!/usr/bin/env python

"""
Application to display the declared time on projects by agents in Hito and to allow validation of
these declarations by the line managers.
"""

import argparse
import os
from datetime import datetime, timedelta

import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output, State
from flask import session

from ositah.app import app
from ositah.apps.analysis import analysis_layout
from ositah.apps.configuration.main import configuration_layout
from ositah.apps.export import export_layout
from ositah.apps.validation.main import validation_layout
from ositah.utils.agents import get_agent_by_email
from ositah.utils.authentication import (
    LOGIN_URL,
    LOGOUT_URL,
    SESSION_MAX_DURATION,
    configure_multipass_ldap,
    identity_list,
    multipass,
    protect_views,
)
from ositah.utils.menus import (
    TEAM_SELECTED_VALUE_ID,
    TEAM_SELECTION_DATE_ID,
    VALIDATION_PERIOD_SELECTED_ID,
    ositah_jumbotron,
)
from ositah.utils.utils import (
    AUTHORIZED_ROLES,
    HITO_ROLE_TEAM_MGR,
    TEAM_LIST_ALL_AGENTS,
    GlobalParams,
    define_config_params,
)

# Minimum role to access the configuration page
CONFIGURATION_MIN_ROLE = HITO_ROLE_TEAM_MGR

CONFIG_FILE_NAME_DEFAULT = "ositah.cfg"

SIDEBAR_WIDTH = 16
SIDEBAR_HREF_HOME = "/"
SIDEBAR_HREF_ANALYSIS = "/analysis"
SIDEBAR_HREF_CONFIGURATION = "/configuration"
SIDEBAR_HREF_NSIP_EXPORT = "/export"
SIDEBAR_HREF_VALIDATION = "/validation"
# SIDEBAR_HREF_ALL entry order must match render_page_content callback
# output order
SIDEBAR_HREF_ALL = [
    SIDEBAR_HREF_ANALYSIS,
    SIDEBAR_HREF_CONFIGURATION,
    SIDEBAR_HREF_NSIP_EXPORT,
    SIDEBAR_HREF_VALIDATION,
    LOGOUT_URL,
    SIDEBAR_HREF_HOME,
    LOGIN_URL,
]

MENU_ID_ANALYSIS = "analysis-menu"
MENU_ID_CONFIGURATION = "configuration-menu"
MENU_ID_EXPORT = "export-menu"
MENU_ID_HOME = "home-menu"
MENU_ID_LOGIN = "login-menu"
MENU_ID_LOGOUT = "logout-menu"
MENU_ID_VALIDATION = "validation-menu"


# the style arguments for the sidebar. We use position:fixed and a fixed width
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": f"{SIDEBAR_WIDTH}rem",
    "padding": "2rem 1rem",
    "backgroundColor": "#f8f9fa",
}

# the styles for the main content position it to the right of the sidebar and
# add some padding.
CONTENT_STYLE = {
    "marginLeft": f"{SIDEBAR_WIDTH+2}rem",
    "marginRight": "2rem",
    "padding": "2rem 1rem",
}


# Get default configuration file: look first in the current directory and if not
# found use the application directory.
def default_config_path() -> str:
    config_file = f"{os.getcwd()}/{CONFIG_FILE_NAME_DEFAULT}"
    if not os.path.exists(config_file):
        config_file = f"{os.path.dirname(os.path.abspath(__file__))}/{CONFIG_FILE_NAME_DEFAULT}"

    return config_file


# URL not found jumbotron
def url_not_found(path):
    return ositah_jumbotron(
        "404: Not found",
        f"URL {path} was not recognised...",
        title_class="text-danger",
    )


# valid role missing jumbotron
def valid_role_missing(msg):
    return ositah_jumbotron(
        "You don't have a valid Hito role to OSITAH",
        msg,
        title_class="text-warning",
    )


@app.callback(
    [
        Output("page-content", "children"),
        Output("login-info", "children"),
        #  Output order must match SIDEBAR_HREF_ALL entry order
        Output(MENU_ID_ANALYSIS, "disabled"),
        Output(MENU_ID_CONFIGURATION, "disabled"),
        Output(MENU_ID_EXPORT, "disabled"),
        Output(MENU_ID_VALIDATION, "disabled"),
        Output(MENU_ID_LOGOUT, "disabled"),
    ],
    Input("url", "pathname"),
    State("login-info", "children"),
)
def render_page_content(pathname, login_menu):
    """
    Function called to render the main page in OSITAH. It is also in charge of managing user
    sessions.

    :param pathname:
    :param login_menu:
    :return: callback output
    """

    from ositah.utils.authentication import remove_session
    from ositah.utils.hito_db import get_db, new_uuid
    from ositah.utils.hito_db_model import OSITAHSession, Team

    global_params = GlobalParams()
    logged_in_user = login_menu
    menus_disabled = True

    db = get_db()
    OSITAHSession.__table__.create(db.session.bind, checkfirst=True)

    user_authenticated = False
    if "user_id" in session:
        # 'user_id' is defined by Multipass if the login was successful
        if "uid" in session and "user_email" in session:
            # The user already logged in successfully once, check if the session is among the known
            # valid sessions. As id and email columns have a unique constraint, the query can
            # return only 0 or 1 value
            saved_session = OSITAHSession.query.filter(
                OSITAHSession.id == str(session["uid"]),
                OSITAHSession.email == session["user_email"],
            ).first()
            if saved_session:
                current_time = datetime.now()
                if current_time > saved_session.last_use + timedelta(hours=SESSION_MAX_DURATION):
                    remove_session()
                else:
                    saved_session.last_use = current_time
                    db.session.commit()
                    user_authenticated = True
        if not user_authenticated and session["user_id"] in identity_list:
            # Session has been fully initialized yet: do it and save it
            session["user_email"] = identity_list[session["user_id"]].email
            session["uid"] = new_uuid()
            this_session = OSITAHSession(
                id=str(session["uid"]),
                email=session["user_email"],
                last_use=datetime.now(),
            )
            db.session.add(this_session)
            db.session.commit()
            user_authenticated = True

    if user_authenticated:
        user_session_data = global_params.session_data
        user = get_agent_by_email()
        role_ok = False
        user_roles = user.roles
        for role in AUTHORIZED_ROLES:
            if role in user_roles:
                role_ok = True
                user_session_data.role = role
                break
        if role_ok:
            if not user_session_data.agent_teams:
                if role == HITO_ROLE_TEAM_MGR:
                    # For a team manager, show only the teams he/she is a manager
                    teams = Team.query.filter(Team.managers.any(email=session["user_email"])).all()
                    if len(teams) == 0:
                        # A user with role ROLE_RESP but is not the manager of any team is degraded
                        # to ROLE_AGENT
                        role_ok = False
                        role_not_ok_msg = (
                            f"{user.prenom} {user.nom} n'est" " responsable d'aucune équipe"
                        )
                        team_list = []
                    else:
                        teams.extend(
                            Team.query.filter(
                                Team.children_managers.any(email=session["user_email"])
                            ).all()
                        )
                        team_list = sorted([t.nom for t in teams])
                else:
                    # For other allowed roles, show all teams and add an entry for all agents
                    teams = Team.query.all()
                    team_list = sorted([t.nom for t in teams])
                    team_list.insert(0, TEAM_LIST_ALL_AGENTS)
                user_session_data.add_teams(team_list, sort_list=False)
            logged_in_user = f"logged in as {user.prenom} {user.nom}"
            menus_disabled = False
        else:
            role_not_ok_msg = (
                f"{user.prenom} {user.nom} n'a pas de role Hito approprié"
                " ({', '.join(AUTHORIZED_ROLES)})"
            )
    else:
        logged_in_user = login_menu_link()
        role_ok = True

    return_values = [logged_in_user]
    for i in range(len(SIDEBAR_HREF_ALL) - 2):
        if (
            SIDEBAR_HREF_ALL[i] == SIDEBAR_HREF_CONFIGURATION
            and user_authenticated
            and AUTHORIZED_ROLES.index(user_session_data.role)
            > AUTHORIZED_ROLES.index(CONFIGURATION_MIN_ROLE)
        ):
            disable_flag = True
        else:
            disable_flag = menus_disabled
        return_values.append(disable_flag)
    if not role_ok:
        return_values.insert(0, valid_role_missing(role_not_ok_msg))
        return return_values

    if user_authenticated:
        if pathname == SIDEBAR_HREF_VALIDATION:
            return_values.insert(0, validation_layout())
            return return_values
        elif pathname == SIDEBAR_HREF_ANALYSIS:
            return_values.insert(0, analysis_layout())
            return return_values
        elif pathname == SIDEBAR_HREF_NSIP_EXPORT:
            return_values.insert(0, export_layout())
            return return_values
        elif pathname == SIDEBAR_HREF_CONFIGURATION:
            return_values.insert(0, configuration_layout())
            return return_values

    # Display the same message based on the login state for all valid URLs if none matched
    # previously
    if pathname in SIDEBAR_HREF_ALL:
        if user_authenticated:
            return_values.insert(
                0,
                html.P("Sélectionner ce que vous souhaitez faire dans le menu principal"),
            )
        else:
            return_values.insert(0, html.P("Veuillez vous authentifier"))
        return return_values

    # If the user tries to reach a different page, return a 404 message
    return_values.insert(0, url_not_found(pathname))
    return return_values


def login_menu_link():
    """
    :return: graphic object for login menu
    """

    return dbc.NavLink("Login", id=MENU_ID_LOGIN, href=LOGIN_URL, external_link=True)


def make_app(environ=None, start_response=None, options=None):
    """
    Function to create the application without running it. It is the main entry point when called
    as a uWSGI application (from gunicorn or uwswgi for example). Must return the Flask application
    server.

    :param environ: environment variables received from the uWSGI server
    :param start_response: function received from the uWSGI server (not used)
    :param options: parser options (will be initialized to sensible values when called from a uSWGI
                    server)
    :return: Flask application server
    """

    # Initialize options to sensible values: required when called from a uWSGI server
    if options is None:
        options = argparse.Namespace()
        options.configuration_file = default_config_path()
        options.debug = True

    config = define_config_params(options.configuration_file)

    configure_multipass_ldap(app.server, config["server"]["authentication"]["provider_name"])
    multipass.init_app(app.server)

    app.server.secret_key = "ositah-dashboard"

    protect_views(app)

    # Import from hito_db must not be done after configuration has been loaded
    from ositah.utils.hito_db import get_db

    # Initialize DB connection by calling get_db()
    get_db(init_session=False)

    sidebar = html.Div(
        [
            html.H2("OSITAH", className="display-4"),
            html.Hr(),
            html.P("Suivi des déclarations de temps", className="lead"),
            dbc.Nav(
                [
                    # external_link=True is required for the callback on dcc.Location to work
                    html.Div(login_menu_link(), id="login-info"),
                    dbc.NavLink(
                        "Logout",
                        id=MENU_ID_LOGOUT,
                        href=LOGOUT_URL,
                        disabled=True,
                        external_link=True,
                    ),
                ],
                vertical="md",
            ),
            html.Hr(),
            dbc.Nav(
                [
                    dbc.NavLink(
                        "Home",
                        id=MENU_ID_HOME,
                        href=SIDEBAR_HREF_HOME,
                        active="exact",
                    ),
                    dbc.NavLink(
                        "Suvi / Validation",
                        id=MENU_ID_VALIDATION,
                        href=SIDEBAR_HREF_VALIDATION,
                        active="exact",
                        disabled=True,
                    ),
                    dbc.NavLink(
                        "Analyse",
                        id=MENU_ID_ANALYSIS,
                        href=SIDEBAR_HREF_ANALYSIS,
                        active="exact",
                        disabled=True,
                    ),
                    dbc.NavLink(
                        "Export NSIP",
                        id=MENU_ID_EXPORT,
                        href=SIDEBAR_HREF_NSIP_EXPORT,
                        active="exact",
                        disabled=True,
                    ),
                    dbc.NavLink(
                        "Configuration",
                        id=MENU_ID_CONFIGURATION,
                        href=SIDEBAR_HREF_CONFIGURATION,
                        active="exact",
                        disabled=True,
                    ),
                ],
                vertical="md",
                pills=True,
            ),
            dcc.Store(id=TEAM_SELECTED_VALUE_ID, data=""),
            dcc.Store(id=TEAM_SELECTION_DATE_ID, data=""),
            dcc.Store(id=VALIDATION_PERIOD_SELECTED_ID, data=""),
        ],
        style=SIDEBAR_STYLE,
    )

    content = html.Div(id="page-content", style=CONTENT_STYLE)

    app.layout = html.Div([dcc.Location(id="url"), sidebar, content])

    return app.server


def main():
    """
    Main entry point when executing the application from the command line

    :return: exit status
    """

    global_params = GlobalParams()

    DEBUG_DASH = "dash"
    DEBUG_SQLALCHEMY = "db"
    DEBUG_ALL = "all"
    DEBUG_NONE = "none"

    # parser must be run here to avoid messing up with gunicorn
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--configuration-file",
        default=default_config_path(),
        help=f"Configuration file (D: {default_config_path()})",
    )
    parser.add_argument(
        "--debug",
        choices=[DEBUG_DASH, DEBUG_SQLALCHEMY, DEBUG_ALL, DEBUG_NONE],
        default=DEBUG_NONE,
        help="Enable debugging mode in Dash and/or SQLAlchemy (do not use in production)",
    )
    options = parser.parse_args()

    dash_debug = False
    sqlalchemy_debug = False
    if options.debug == DEBUG_DASH or options.debug == DEBUG_ALL:
        dash_debug = True
    if options.debug == DEBUG_SQLALCHEMY or options.debug == DEBUG_ALL:
        sqlalchemy_debug = "debug"

    make_app(options=options)

    # If --debug, enable SQLAlchemy verbose mode
    if sqlalchemy_debug:
        app.server.config["SQLALCHEMY_ECHO"] = True

    app.run_server(debug=dash_debug, port=global_params.port)


if __name__ == "__main__":
    exit(main())

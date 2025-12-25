# Helper functions to interact with the agent table
import pandas as pd
from flask import session

from ositah.utils.exceptions import SessionDataMissing
from ositah.utils.utils import TEAM_LIST_ALL_AGENTS, GlobalParams, no_session_id_jumbotron

NSIP_AGENT_COLUMNS = {
    "email_reseda": "email_reseda",
    "firstname": "firstname",
    "lastname": "lastname",
}


def get_agent_by_email(agent_email: str = None) -> str:
    """
    Retrieve an agent from Hito using his email. If the agent email argument
    is not present, use the session user_email attribute.

    :param: agent_email: agent's email
    :return: agent entry (row)
    """

    from ositah.utils.hito_db_model import Agent

    if agent_email is None:
        agent_email = session["user_email"]
    user = Agent.query.filter_by(email_auth=agent_email).first()
    if user is None:
        user = Agent.query.filter_by(email=session["user_email"]).first()

    return user


def get_agents(period_date: str, team: str = None) -> pd.DataFrame:
    """
    Read agent table in Hito database and return it as a dataframe. If a cached version exists,
    use it.

    :param period_date: a date that must be inside the declaration period
    :param team: selected team (and subteams). Ignored if None or TEAM_LIST_ALL_AGENTS.
    :return: dataframe
    """

    from ositah.utils.hito_db import get_db

    global_params = GlobalParams()
    columns = global_params.columns
    db = get_db()

    try:
        session_data = global_params.session_data
    except SessionDataMissing:
        return no_session_id_jumbotron()

    # start_date, _ = get_validation_period_dates(period_date)

    agents = session_data.agent_list
    if agents is None:
        agent_list = pd.read_sql_query(global_params.agent_query, con=db.engine)
        # WIP ; attempt to refine the agent list taking into account arrival and departure date
        # Difficulty: carriere table has a suboptimal structure making a SQL request difficult
        # TODO: query separately agent+team and carriere, then use Pandas to join them taking all
        # the criteria into account
        # Ignore archived agents that left before the start of the declaration period
        # agent_list = agent_list.loc[(agent_list.archive == 0) |
        #                          (agent_list.date_fin >= start_date.date().isoformat())]
        if team and team != TEAM_LIST_ALL_AGENTS:
            agent_list = agent_list[
                agent_list.team.notna() & agent_list[columns["team"]].str.match(team)
            ]
        else:
            # If the agent doesn't belong to a team, set team to an empty string rather than None
            agent_list.loc[agent_list.team.isna(), "team"] = ""
        agent_list[columns["fullname"]] = agent_list[
            [columns["lastname"], columns["firstname"]]
        ].agg(" ".join, axis=1)
        agent_list.columns = agent_list.columns.str.lower()
        agent_list["statut"] = agent_list["statut"].str.extract("^statut_(.+)$")
        agent_list["optional"] = agent_list["statut"].isin(
            global_params.declaration_options["optional_statutes"]
        )
        agent_list["email_auth"] = agent_list["email_auth"].str.lower()
        team_list = pd.DataFrame(agent_list[columns["team"]].unique(), columns=["name"])
        optional_teams_list = []
        for opt_team in global_params.declaration_options["optional_teams"]:
            optional_teams_list.append(
                team_list[team_list["name"].str.match(opt_team, case=False, na=False)]["name"]
            )
        optional_teams = pd.concat(optional_teams_list)
        agent_list.loc[~agent_list["optional"], "optional"] = agent_list["team"].isin(
            optional_teams
        )
        session_data.agent_list = agent_list
    else:
        agent_list = session_data.agent_list

    return agent_list


def get_nsip_agents():
    """
    Retrieve agents from NSIP and return them in a dataframe.

    :return: dataframe or None if NSIP is not configured
    """

    global_params = GlobalParams()

    if global_params.nsip:
        agents = pd.DataFrame.from_dict(global_params.nsip.get_agent_list())
        columns_to_delete = []
        for c in agents.columns.tolist():
            if c not in NSIP_AGENT_COLUMNS.values():
                columns_to_delete.append(c)
        agents["fullname"] = agents[
            [NSIP_AGENT_COLUMNS["lastname"], NSIP_AGENT_COLUMNS["firstname"]]
        ].agg(" ".join, axis=1)
        agents.drop(columns=columns_to_delete, inplace=True)

        return agents

    else:
        return None

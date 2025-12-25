import re
from typing import Dict, List

import pandas as pd


def get_hito_teams():
    """
    Return Hito teams as a Dataframe

    :return: Hito teams
    """

    from .hito_db_model import Team, db

    team_query = Team.query

    teams = pd.read_sql(team_query.statement, con=db.session.bind)

    return teams


def get_project_team_ids(team_config: Dict[str, str], project: str) -> List[str]:
    """
    Return the list of team ID associated with the project based on the configuration passed.
    The configuration is a dict where the key is a pattern applied to the project name and
    the value is the list of team names.

    :param team_config: dict describing the teams associated with a project
    :param project: project name
    :return: list of team ids or None if no match is found
    """

    for pattern, team_list in team_config.items():
        if re.match(pattern, project):
            hito_teams = get_hito_teams()
            hito_teams["selected"] = False
            for team_pattern in team_list:
                hito_teams.loc[hito_teams.nom.str.match(f"{team_pattern}$"), "selected"] = True
            return hito_teams["id"].to_list()

    return None

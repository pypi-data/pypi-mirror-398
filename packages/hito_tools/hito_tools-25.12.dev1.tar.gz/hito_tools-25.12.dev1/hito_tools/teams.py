from typing import Dict

TEAM_CSV_TEAM_ID = "id"
TEAM_CSV_TEAM_NAME = "name"
NSIP_NO_TEAM_ID = "770"


class Team:
    def __init__(self, name: str, id: str) -> None:
        self._name = name
        self._id = id

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name


def get_nsip_team_ids(nsip_session) -> Dict[str, Team]:
    """
    Return the team list read from NSIP as a dict where the key is the team name and
    the value a Team object. The team name is the friendlyName attribute if defined, else
    the name attribute.

    :return: dict
    """

    teams = {}
    team_list = nsip_session.get_teams()
    for t in team_list:
        if "friendlyName" in t and t["friendlyName"]:
            team_name = t["friendlyName"]
        else:
            team_name = t["name"]
        teams[team_name] = Team(team_name, t["id"])

    return teams

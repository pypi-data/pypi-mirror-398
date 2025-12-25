import csv
import re
from typing import Dict, Set

from .agents import Agent

NSIP_ACTIVIY_NAME = "name"
NSIP_ACTIVITY_ID = "id"
NSIP_ACTIVIY_TYPE = "type"
NSIP_MASTERPROJECT_FIELD = "Master projet"
NSIP_PROJECT_FIELD = "Projet"
NSIP_PROJECT_ID_FIELD = "id projet"

LOCAL_MASTERPROJECT_NAME = "Local projects"
LOCAL_PROJECT_NAME_FIELD = "PROJET"
LOCAL_CSV_LAST_FIELD_BEFORE_AGENTS = "TOTAL \nnb semaines"


class ProjectActivity:
    def __init__(self, master_project: str, project_name: str, nsip_id: str = None) -> None:
        # Ensure that the project name in Hito starts by the master project name to ensure unicity.
        # Use / as separator between master project and project names (used by Hito to identify
        # project groups)
        m = re.match(rf"{master_project}\s+\-\s+(?P<project>.*)", project_name)
        if m:
            project_name = m.group("project")
        if len(master_project) == 0:
            self._name = project_name
        elif len(project_name) == 0:
            self._name = master_project
        else:
            self._name = f"{master_project} / {project_name}"
        self._id = nsip_id

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name


class Project(ProjectActivity):
    def __init__(self, masterproject: str, project: str, nsip_id: str = None) -> None:
        super(Project, self).__init__(masterproject, project, nsip_id)
        self._teams = set()

    @property
    def teams(self) -> Set:
        return self._teams

    @teams.setter
    def teams(self, name: str) -> None:
        self._teams.add(name)


def read_nsip_projects(file: str) -> Dict[str, ProjectActivity]:
    """
    Read a NSIP projects CSV file and return the project list as a dict where the key is the
    project name and the value is a Project object.

    :param file: NSIP project CSV
    :return: list of projects as a dict
    """

    project_list: Dict[str, ProjectActivity] = {}

    try:
        with open(file, "r", encoding="utf-8") as f:
            nsip_reader = csv.DictReader(f, delimiter=";")
            for e in nsip_reader:
                project = Project(
                    e[NSIP_MASTERPROJECT_FIELD],
                    e[NSIP_PROJECT_FIELD],
                    e[NSIP_PROJECT_ID_FIELD],
                )
                project_list[e[NSIP_PROJECT_ID_FIELD]] = project
    except:  # noqa: E722
        print(f"Error reading NSIP projects CSV ({file})")
        raise

    return project_list


def read_nsip_activities(
    file: str, masterproject_names: Dict[str, str] = {}
) -> Dict[str, ProjectActivity]:
    """
    Read a NSIP activities CSV file and return the activity list as a dict where the key is
    the activity name and the value is a Project object. The master project is derived from
    the activity type, the actual name being defined in the configuration. When the actual name
    is None, the category is disabled.

    :param file: NSIP project CSV
    :param masterproject_names: a dict that defines the actual name of a NSIP category or disable
                                its use.
    :return: list of projects as a dict
    """

    project_list: Dict[str, ProjectActivity] = {}

    try:
        with open(file, "r", encoding="utf-8") as f:
            nsip_reader = csv.DictReader(f, delimiter=";")
            for e in nsip_reader:
                m = re.match(r"(?P<category>.*)reference$", e[NSIP_ACTIVIY_TYPE])
                if m:
                    category = m.group("category")
                else:
                    category = e[NSIP_ACTIVIY_TYPE]
                if category in masterproject_names:
                    master_project = masterproject_names[category]
                    if master_project is None:
                        continue
                else:
                    master_project = category
                project = Project(master_project, e[NSIP_ACTIVIY_NAME], e[NSIP_ACTIVITY_ID])
                project_list[project.name] = project
    except:  # noqa: E722
        print(f"Error reading NSIP activities CSV ({file})")
        raise

    return project_list


def read_local_projects(file: str) -> Dict[str, ProjectActivity]:
    """
    Read the CSV of local projects maintained by CeMaP and return the project list and agent list.
    The project list is as a dict where the key is the project name and the value is a Project
    object. In this CSV, agents assigned to projects are column names.

    :param file: local project CSV
    :return: list of projects as a dict
    """

    project_list: Dict[str, ProjectActivity] = {}
    agent_list: Dict[str, Agent] = {}

    try:
        with open(file, "r", encoding="utf-8") as f:
            nsip_reader = csv.DictReader(f, delimiter=";")
            agents_found = False

            # Retrieve agents
            for field in nsip_reader.fieldnames:
                if agents_found:
                    agent = Agent("", field)
                    agent_list[agent.get_fullname()] = agent
                elif field == LOCAL_CSV_LAST_FIELD_BEFORE_AGENTS:
                    agents_found = True
            if len(agent_list.keys()) == 0:
                raise Exception(
                    (
                        f"Malformed CSV for local projects: column"
                        f" '{LOCAL_CSV_LAST_FIELD_BEFORE_AGENTS}' missing"
                    )
                )

            # Retrieve projects and set the project list for each agent
            # Ignore entries with an empty project name
            for e in nsip_reader:
                if len(e[LOCAL_PROJECT_NAME_FIELD]) == 0:
                    continue
                project = Project(LOCAL_MASTERPROJECT_NAME, e[LOCAL_PROJECT_NAME_FIELD])
                project_list[project.name] = project
                for agent in agent_list.values():
                    if e[agent.get_fullname()]:
                        agent.add_project(project.name)

    except:  # noqa: E722
        print(f"Error reading NSIP projects CSV ({file})")
        raise

    return project_list, agent_list

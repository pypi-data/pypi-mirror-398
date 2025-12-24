"""
Projects in EZOffice
"""

import logging
import os
import time
from datetime import date
from typing import Literal

from ezoff._auth import Decorators
from ezoff._helpers import http_post, http_get, http_patch
from ezoff.data_model import Project

logger = logging.getLogger(__name__)


@Decorators.check_env_vars
def project_create(
    name: str,
    description: str | None = None,
    identifier: str | None = None,
    expected_start_date: date | None = None,
    expected_end_date: date | None = None,
    linked_modules: (
        Literal[
            "items",
            "checkouts",
            "reservations",
            "purchase_orders",
            "work_orders",
            "carts",
            "locations",
        ]
        | None
    ) = None,
    assigned_user_ids: list[int] | None = None,
) -> Project | None:
    """
    Creates a new project.

    :param name: Name of the project.
    :type name: str
    :param description: Description of the project.
    :type description: str, optional
    :param identifier: Identifier for the project.
    :type identifier: str, optional
    :param expected_start_date: Expected start date of the project.
    :type expected_start_date: date, optional
    :param expected_end_date: Expected end date of the project.
    :type expected_end_date: date, optional
    :param linked_modules: Modules to link to the project.
    :type linked_modules: str, optional
    :param assigned_user_ids: User IDs to assign to the project.
    :type assigned_user_ids: list of int, optional
    :return: The created project or None if creation failed.
    :rtype: Project | None
    """

    params = {k: v for k, v in locals().items() if v is not None}

    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/projects"
    response = http_post(url=url, payload={"project": params}, title="Project Create")

    if response.status_code == 200 and "project" in response.json():
        return Project(**response.json()["project"])
    else:
        return None


@Decorators.check_env_vars
def project_return(project_id: int) -> Project | None:
    """
    Returns a particular project.

    :param project_id: ID of the project to return.
    :type project_id: int
    :return: The requested project or None if not found.
    :rtype: Project | None
    """
    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/projects/{project_id}"
    response = http_get(url=url, title="Project Return")

    if response.status_code == 200 and "project" in response.json():
        return Project(**response.json()["project"])
    else:
        return None


@Decorators.check_env_vars
def projects_return() -> list[Project]:
    """
    Returns all projects.

    :return: A list of all projects.
    :rtype: list[Project]
    """

    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/projects"

    all_projects = []

    while True:
        response = http_get(url=url, title="Projects Return")
        data = response.json()

        if "projects" not in data:
            logger.error(f"Error, could not get projects: {response.content}")
            raise Exception(f"Error, could not get projects: {response.content}")

        all_projects.extend(data["projects"])

        if (
            "metadata" not in data
            or "next_page" not in data["metadata"]
            or data["metadata"]["next_page"] is None
        ):
            break

        # Get the next page's url from the current page of data.
        url = data["metadata"]["next_page"]

        time.sleep(1)

    return [Project(**x) for x in all_projects]


# @Decorators.check_env_vars
# def project_linked_items_return(project_id: int):
#     """
#     Returns objects for a given module linked to a project.
#     # TODO API endpoint seems to just 500 internal server error
#     # in my testing in Postman.
#     """


@Decorators.check_env_vars
def project_mark_complete(project_id: int) -> Project | None:
    """
    Mark a project as complete.

    :param project_id: ID of the project to mark as complete.
    :type project_id: int
    :return: The updated project or None if marking complete failed.
    :rtype: Project | None
    """

    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/projects/{project_id}/mark_complete"
    response = http_patch(url=url, title="Project Mark Complete")

    if response.status_code == 200 and "project" in response.json():
        return Project(**response.json()["project"])
    else:
        return None


@Decorators.check_env_vars
def project_mark_in_progress(project_id: int) -> Project | None:
    """
    Mark a project as in progress.

    :param project_id: ID of the project to mark as in progress.
    :type project_id: int
    :return: The updated project or None if marking in progress failed.
    :rtype: Project | None
    """

    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/projects/{project_id}/mark_in_progress"
    response = http_patch(url=url, title="Project Mark In-Progress")

    if response.status_code == 200 and "project" in response.json():
        return Project(**response.json()["project"])
    else:
        return None

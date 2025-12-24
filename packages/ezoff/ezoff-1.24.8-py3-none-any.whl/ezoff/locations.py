"""
This module contains functions for interacting with locations in EZOfficeInventory
"""

import logging
import os
import time
from typing import Literal

from ezoff._auth import Decorators
from ezoff._helpers import http_post, http_get, http_patch
from ezoff.data_model import Location

logger = logging.getLogger(__name__)


@Decorators.check_env_vars
def location_create(
    name: str,
    city: str | None = None,
    status: str | None = None,
    street1: str | None = None,
    street2: str | None = None,
    state: str | None = None,
    zip_code: str | None = None,
    description: str | None = None,
    parent_id: int | None = None,
    latitude: int | None = None,
    longitude: int | None = None,
    country: str | None = None,
    identification_number: str | None = None,
    manual_coordinates_provided: bool | None = None,
    default_return_duration: int | None = None,
    default_return_deuration_unit: str | None = None,
    default_return_time: str | None = None,
    apply_default_return_date_to_child_locations: bool | None = None,
    custom_fields: list[dict] | None = None,
) -> Location | None:
    """
    Creates a new location.

    :param name: Name of the location
    :type name: str
    :param city: City where the location is situated
    :type city: str, optional
    :param status: Status of the location (e.g., 'active', 'inactive')
    :type status: str, optional
    :param street1: First line of the street address
    :type street1: str, optional
    :param street2: Second line of the street address
    :type street2: str, optional
    :param state: State where the location is situated
    :type state: str, optional
    :param zip_code: ZIP code of the location
    :type zip_code: str, optional
    :param description: Description of the location
    :type description: str, optional
    :param parent_id: ID of the parent location, if any
    :type parent_id: int, optional
    :param latitude: Latitude coordinate of the location
    :type latitude: int, optional
    :param longitude: Longitude coordinate of the location
    :type longitude: int, optional
    :param country: Country where the location is situated
    :type country: str, optional
    :param identification_number: Identification number for the location
    :type identification_number: str, optional
    :param manual_coordinates_provided: Whether manual coordinates are provided
    :type manual_coordinates_provided: bool, optional
    :param default_return_duration: Default return duration for items at this location
    :type default_return_duration: int, optional
    :param default_return_deuration_unit: Unit for the default return duration (e.g., 'days', 'weeks')
    :type default_return_deuration_unit: str, optional
    :param default_return_time: Default return time for items at this location
    :type default_return_time: str, optional
    :param apply_default_return_date_to_child_locations: Whether to apply default return date to child
    :type apply_default_return_date_to_child_locations: bool, optional
    :param custom_fields: List of custom fields for the location
    :type custom_fields: list of dict, optional
    :return: The created location, or None if creation failed
    :rtype: Location | None
    """

    params = {k: v for k, v in locals().items() if v is not None}

    url = (
        f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/locations"
    )
    payload = {"location": params}
    response = http_post(url=url, payload=payload, title="Location Create")

    if response.status_code == 200 and "location" in response.json():
        return Location(**response.json()["location"])
    else:
        return None


@Decorators.check_env_vars
def location_return(location_id: int) -> Location | None:
    """
    Returns a particular location.

    :param location_id: The ID of the location to return
    :type location_id: int
    :return: The location with the specified ID, or None if not found
    :rtype: Location | None
    """

    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/locations/{location_id}"
    response = http_get(url=url, title="Location Return")

    if response.status_code == 200 and "location" in response.json():
        return Location(**response.json()["location"])
    else:
        return None


@Decorators.check_env_vars
def locations_return(
    state: Literal["active", "inactive"] | None = None,
    filter: dict = None,
) -> list[Location]:
    """
    Returns all locations. Optionally filter by state (active, inactive).
    Note: Unfortunately, EZO doesn't appear to have any further filtering options
    for the locations endpoint, only state. Otherwise, a more generic filter_data
    parameter would be used here.
    Optional filter parameter is for compatibility with ezo_cache class.

    :param state: Filter locations by state ('active', 'inactive')
    :type state: str, optional
    :param filter: Raw filter json for EZO API.
    :type filter: dict, optional
    :return: A list of all locations
    :rtype: list of Location
    """
    if state is not None and filter is not None:
        raise ValueError(
            "State and filter are mutually exclusive options for ezoff.locations_return()"
        )

    if state is not None:
        filter_data = {"filters": {"state": state}}
    elif filter is not None:
        filter_data = {"filters": filter}
    else:
        filter_data = None

    url = (
        f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/locations"
    )

    all_locations = []
    while True:
        response = http_get(url=url, payload=filter_data, title="Locations Return")
        data = response.json()

        if "locations" not in data:
            logger.error(f"Error, could not get locations: {data}")
            raise Exception(f"Error, could not get locations: {response.content}")

        all_locations.extend(data["locations"])

        if (
            "metadata" not in data
            or "next_page" not in data["metadata"]
            or data["metadata"]["next_page"] is None
        ):
            break

        # Get the next page's url from the current page of data.
        url = data["metadata"]["next_page"]

        # Potentially running into rate limiting issues with this endpoint
        # Sleep for a second to avoid this
        time.sleep(1)

    return [Location(**x) for x in all_locations]


@Decorators.check_env_vars
def location_activate(
    location_id: int, activate_children: bool | None = None
) -> Location | None:
    """
    Activates a particular location.

    :param location_id: The ID of the location to activate
    :type location_id: int
    :param activate_children: Whether to activate all child locations as well
    :type activate_children: bool, optional
    :return: The activated location, or None if activation failed
    :rtype: Location | None
    """

    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/locations/{location_id}/activate"

    if activate_children:
        data = {"location": {"activate_all_children_locations": True}}
    else:
        data = None

    response = http_patch(url=url, payload=data, title="Location Activate")

    if response.status_code == 200 and "location" in response.json():
        return Location(**response.json()["location"])
    else:
        return None


@Decorators.check_env_vars
def location_deactivate(location_id: int) -> Location | None:
    """
    Deactivates a particular location.

    :param location_id: The ID of the location to deactivate
    :type location_id: int
    :return: The deactivated location, or None if deactivation failed
    :rtype: Location | None
    """

    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/locations/{location_id}/deactivate"
    response = http_patch(url=url, title="Location Deactivate")

    if response.status_code == 200 and "location" in response.json():
        return Location(**response.json()["location"])
    else:
        return None


@Decorators.check_env_vars
def location_update(location_id: int, update_data: dict) -> Location | None:
    """
    Updates a particular location.

    :param location_id: The ID of the location to update
    :type location_id: int
    :param update_data: A dictionary of fields to update and their new values
    :type update_data: dict
    :return: The updated location, or None if the update failed
    :rtype: Location | None
    """

    for field in update_data:
        if field not in Location.model_fields:
            raise ValueError(f"'{field}' is not a valid field for a location.")

    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/locations/{location_id}"
    payload = {"location": update_data}
    response = http_patch(url=url, payload=payload, title="Location Deactivate")

    if response.status_code == 200 and "location" in response.json():
        return Location(**response.json()["location"])
    else:
        return None

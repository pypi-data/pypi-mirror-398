"""
This module contains functions for interacting with members/roles/user setup in EZOfficeInventory
"""

import logging
import os
import time
from typing import Optional

from ezoff._auth import Decorators
from ezoff._helpers import http_get, http_patch

logger = logging.getLogger(__name__)


@Decorators.check_env_vars
def members_return_v1(filter: Optional[dict]) -> list[dict]:
    """
    Get members from EZOfficeInventory
    Optionally filter by email, employee_identification_number, or status
    https://ezo.io/ezofficeinventory/developers/#api-retrieve-members

    :param filter: Dictionary of filter parameters
    :type filter: Optional[dict]
    :return: List of members
    :rtype: list[dict]
    """

    if filter is not None:
        if "filter" not in filter or "filter_val" not in filter:
            raise ValueError("filter must have 'filter' and 'filter_val' keys")

        if filter["filter"] not in [
            "email",
            "employee_identification_number",
            "status",
        ]:
            raise ValueError(
                "filter['filter'] must be one of 'email', 'employee_identification_number', 'status'"
            )

    # url = os.environ["EZO_BASE_URL"] + "members.api"
    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/members.api"

    page = 1
    all_members = []

    while True:
        params = {"page": page, "include_custom_fields": "true"}
        if filter is not None:
            params.update(filter)

        response = http_get(url=url, params=params, title="Members Return v1")
        data = response.json()

        if "members" not in data:
            logger.error(f"Error, could not get members: {data}")
            raise Exception(f"Error, could not get members: {response.content}")

        all_members.extend(data["members"])

        if "total_pages" not in data:
            break

        if page >= data["total_pages"]:
            break

        page += 1

        # Potentially running into rate limiting issues with this endpoint
        # Sleep for a second to avoid this
        time.sleep(1)

    return all_members


@Decorators.check_env_vars
def member_update_v1(member_id: int, member: dict) -> dict:
    """
    Update a member with v1 API. Re-added this as the v2 member update endpoint
    doesn't yet support changing the location ID field.

    Note: If updating a customer that has an email, you should include the email
    in the member dict. If you don't, it will get removed for some reason. Not sure
    why as I'm using PATCH. So presumably should only be touching the keys that
    are specified.
    https://ezo.io/ezofficeinventory/developers/#api-update-member

    :param member_id: The ID of the member to update
    :type member_id: int
    :param member: Dictionary of member data to update.
    :type member: dict
    :return: The updated member data
    :rtype: dict
    """

    # Remove any keys that are not valid
    valid_keys = [
        "user[email]",
        "user[employee_id]",
        "user[employee_identification_number]",
        "user[role_id]",
        "user[team_id]",
        "user[user_listing_id]",
        "user[first_name]",
        "user[last_name]",
        "user[address_name]",
        "user[address]",
        "user[address_line_2]",
        "user[city]",
        "user[state]",
        "user[country]",
        "user[phone_number]",
        "user[fax]",
        "user[login_enabled]",
        "user[subscribed_to_emails]",
        "user[display_picture]",
        "user[unsubscribed_by_id]",
        "user[authorization_amount]",
        "user[vendor_id]",
        "user[time_zone]",
        "user[hourly_rate]",
        "user[offboarding_date]",
        "user[location_id]",
        "user[default_address_id]",
        "user[description]",
        "user[department]",
        "skip_confirmation_email",
    ]

    # Check for custom attributes
    member = {
        k: v
        for k, v in member.items()
        if k in valid_keys or k.startswith("user[custom_attributes]")
    }

    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/members/{member_id}.api"
    # member was being passed to data param of requests.patch. might need to address.
    response = http_patch(url=url, json=member, title="Member Update v1")

    return response.json()

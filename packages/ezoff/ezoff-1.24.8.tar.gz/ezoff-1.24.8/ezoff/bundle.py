import logging
import os
import time

from ezoff._auth import Decorators
from ezoff._helpers import http_post, http_get
from ezoff.data_model import Bundle

logger = logging.getLogger(__name__)


@Decorators.check_env_vars
def bundle_create(
    name: str,
    description: str,
    identification_number: str,
    location_id: int,
    enable_items_restricted_by_location: bool,
    bundle_line_items: list[dict],
    allow_add_bundle_without_specifying_items: bool,
) -> Bundle | None:
    """
    Creates a new bundle of items.

    :param name: The name of the bundle.
    :type name: str
    :param description: A description of the bundle.
    :type description: str
    :param identification_number: A unique identification number for the bundle.
    :type identification_number: str
    :param location_id: The ID of the location the bundle is associated with.
    :type location_id: int
    :param enable_items_restricted_by_location: Whether to enable items restricted by location.
    :type enable_items_restricted_by_location: bool
    :param bundle_line_items: A list of dictionaries representing the items in the bundle.
    :type bundle_line_items: list[dict]
    :param allow_add_bundle_without_specifying_items: Whether to allow adding the bundle without specifying items.
    :type allow_add_bundle_without_specifying_items: bool
    :return: The created Bundle object if successful, else None.
    :rtype: Bundle | None
    """
    params = {k: v for k, v in locals().items() if v is not None}

    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/bundles"
    response = http_post(url=url, payload={"bundle": params}, title="Bundle Create")

    if response.status_code == 200 and "bundle" in response.json():
        return Bundle(**response.json()["bundle"])
    else:
        return None


@Decorators.check_env_vars
def bundle_return(bundle_id: int) -> Bundle | None:
    """
    Returns a particular bundle.

    :param bundle_id: The ID of the bundle to retrieve.
    :type bundle_id: int
    :return: The Bundle object if found, else None.
    :rtype: Bundle | None
    """
    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/bundles/{bundle_id}"
    response = http_get(url=url)

    if response.status_code == 200 and "bundle" in response.json():
        return Bundle(**response.json()["bundle"])
    else:
        return None


@Decorators.check_env_vars
def bundles_return(filter: dict | None = None) -> list[Bundle]:
    """
    Returns all bundles.

    :param filter: A dictionary of bundle fields and the values to filter by.
    :type filter: dict, optional
    :return: A list of Bundle objects.
    :rtype: list[Bundle]
    """
    if filter:
        for field in filter:
            if field not in Bundle.model_fields:
                raise ValueError(f"'{field}' is not a valid field for a bundle.")
        filter = {"filters": filter}
    else:
        filter = None

    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/bundles"

    all_bundles = []

    while True:
        response = http_get(url=url, payload=filter, title="Bundles Return")
        data = response.json()

        if "bundles" not in data:
            logger.error(f"Error, could not get bundles: {response.content}")
            raise Exception(f"Error, could not get bundles: {response.content}")

        all_bundles.extend(data["bundles"])

        if (
            "metadata" not in data
            or "next_page" not in data["metadata"]
            or data["metadata"]["next_page"] is None
        ):
            break

        # Get the next page's url from the current page of data.
        url = data["metadata"]["next_page"]

        time.sleep(1)

    return [Bundle(**x) for x in all_bundles]

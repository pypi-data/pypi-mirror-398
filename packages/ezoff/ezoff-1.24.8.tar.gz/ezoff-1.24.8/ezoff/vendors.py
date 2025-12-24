import logging
import os
import time

from ezoff._auth import Decorators
from ezoff._helpers import http_post, http_get, http_patch
from ezoff.data_model import Vendor

logger = logging.getLogger(__name__)


@Decorators.check_env_vars
def vendor_create(
    name: str,
    address: str | None = None,
    description: str | None = None,
    email: str | None = None,
    fax: str | None = None,
    phone: str | None = None,
    website: str | None = None,
    contact_person_name: str | None = None,
    status: bool | None = None,
    custom_fields: list[dict] | None = None,
) -> Vendor | None:
    """
    Creates a new vendor.

    :param name: The name of the vendor.
    :type name: str
    :param address: The address of the vendor.
    :type address: str, optional
    :param description: A description of the vendor.
    :type description: str, optional
    :param email: The email address of the vendor.
    :type email: str, optional
    :param fax: The fax number of the vendor.
    :type fax: str, optional
    :param phone: The phone number of the vendor.
    :type phone: str, optional
    :param website: The website of the vendor.
    :type website: str, optional
    :param contact_person_name: The name of the contact person for the vendor.
    :type contact_person_name: str, optional
    :param status: The status of the vendor. True for active, False for inactive.
    :type status: bool, optional
    :param custom_fields: List of custom fields to set on the vendor. Each item in
        the list should be a dictionary with 'id' and 'value' keys.
    :type custom_fields: list[dict], optional
    :return: The created vendor object if successful, else None.
    :rtype: Vendor | None
    """
    params = {k: v for k, v in locals().items() if v is not None}

    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/vendors"
    response = http_post(url=url, payload={"vendor": params}, title="Vendor Create")

    if response.status_code == 200 and "vendor" in response.json():
        return Vendor(**response.json()["vendor"])
    else:
        return None


@Decorators.check_env_vars
def vendor_return(vendor_id: int) -> Vendor | None:
    """
    Returns a particular vendor.

    :param vendor_id: The ID of the vendor to return.
    :type vendor_id: int
    :return: The vendor object if found, else None.
    :rtype: Vendor | None
    """
    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/vendors/{vendor_id}"
    response = http_get(url=url, title="Vendor Return")

    if response.status_code == 200 and "vendor" in response.json():
        return Vendor(**response.json()["vendor"])
    else:
        return None


@Decorators.check_env_vars
def vendors_return() -> list[Vendor]:
    """
    Returns all vendors.

    :return: List of all vendor objects.
    :rtype: list[Vendor]
    """
    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/vendors"

    all_vendors = []

    while True:
        response = http_get(url=url, title="Vendors Return")
        data = response.json()

        if "vendors" not in data:
            logger.error(f"Error, could not get vendors: {response.content}")
            raise Exception(f"Error, could not get vendors: {response.content}")

        all_vendors.extend(data["vendors"])

        if (
            "metadata" not in data
            or "next_page" not in data["metadata"]
            or data["metadata"]["next_page"] is None
        ):
            break

        # Get the next page's url from the current page of data.
        url = data["metadata"]["next_page"]

        time.sleep(1)

    return [Vendor(**x) for x in all_vendors]


@Decorators.check_env_vars
def vendor_update(vendor_id: int, update_data: dict) -> Vendor | None:
    """
    Updates a particular vendor.

    :param vendor_id: The ID of the vendor to update.
    :type vendor_id: int
    :param update_data: A dictionary of fields to update on the vendor.
    :type update_data: dict
    :return: The updated vendor object if successful, else None.
    :rtype: Vendor | None
    """
    for field in update_data:
        if field not in Vendor.model_fields:
            raise ValueError(f"'{field}' is not a valid field for a vendor.")

    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/vendors/{vendor_id}"
    response = http_patch(
        url=url, payload={"vendor": update_data}, title="Vendor Update"
    )

    if response.status_code == 200 and "vendor" in response.json():
        return Vendor(**response.json()["vendor"])
    else:
        return None

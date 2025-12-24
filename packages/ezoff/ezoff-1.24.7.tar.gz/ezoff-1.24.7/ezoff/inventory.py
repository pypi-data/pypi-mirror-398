"""
Covers everything related to inventory assets.
"""

import logging
import os
import time
from datetime import datetime

from ezoff._auth import Decorators
from ezoff._helpers import (
    http_post,
    http_put,
    http_get,
    http_patch,
    http_delete,
)
from ezoff.data_model import (
    CustomFieldHistoryItem,
    Inventory,
    Reservation,
    ResponseMessages,
    StockHistoryItem,
)

logger = logging.getLogger(__name__)


@Decorators.check_env_vars
def inventory_create(
    name: str,
    group_id: int,
    location_id: int,
    display_image: str | None = None,
    identifier: str | None = None,
    description: str | None = None,
    product_model_number: str | None = None,
    cost_price: float | None = None,
    vendor_id: int | None = None,
    salvage_value: float | None = None,
    sub_group_id: int | None = None,
    inventory_treshold: int | None = None,
    default_low_location_threshold: int | None = None,
    default_excess_location_threshold: int | None = None,
    initial_stock_quantity: int | None = None,
    line_item_atributes: list[dict] | None = None,
    location_thresholds_attributes: list[dict] | None = None,
    asset_detail_attributes: dict | None = None,
    custom_fields: list[dict] | None = None,
) -> Inventory | None:
    """
    Creates a new inventory item.

    :param name: Name of the inventory item
    :type name: str
    :param group_id: ID of the group the inventory item belongs to
    :type group_id: int
    :param location_id: ID of the default location where the inventory item is stored
    :type location_id: int
    :param display_image: URL of the display image for the inventory item
    :type display_image: str, optional
    :param identifier: Unique identifier for the inventory item
    :type identifier: str, optional
    :param description: Description of the inventory item
    :type description: str, optional
    :param product_model_number: Product model number of the inventory item
    :type product_model_number: str, optional
    :param cost_price: Cost price of the inventory item
    :type cost_price: float, optional
    :param vendor_id: ID of the vendor associated with the inventory item
    :type vendor_id: int, optional
    :param salvage_value: Salvage value of the inventory item
    :type salvage_value: float, optional
    :param sub_group_id: ID of the subgroup the inventory item belongs to
    :type sub_group_id: int, optional
    :param inventory_threshold: Inventory threshold for the item
    :type inventory_threshold: int, optional
    :param default_low_location_threshold: Default low location threshold for the item
    :type default_low_location_threshold: int, optional
    :param default_excess_location_threshold: Default excess location threshold for the item
    :type default_excess_location_threshold: int, optional
    :param initial_stock_quantity: Initial stock quantity of the inventory item
    :type initial_stock_quantity: int, optional
    :param line_item_attributes: List of line item attributes for the inventory item
    :type line_item_attributes: list of dict, optional
    :param location_thresholds_attributes: List of location threshold attributes for the inventory item
    :type location_thresholds_attributes: list of dict, optional
    :param asset_detail_attributes: Dictionary of asset detail attributes for the inventory item
    :type asset_detail_attributes: dict, optional
    :param custom_fields: List of custom fields for the inventory item
    :type custom_fields: list of dict, optional
    :return: The created inventory item, or None if creation failed
    :rtype: Inventory | None
    """

    params = {k: v for k, v in locals().items() if v is not None}

    url = (
        f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/inventory"
    )
    response = http_post(
        url=url, payload={"inventory": params}, title="Inventory Create"
    )

    if response.status_code == 200 and "inventory" in response.json():
        return Inventory(**response.json()["inventory"])
    else:
        return None


@Decorators.check_env_vars
def inventory_return(inventory_id: int) -> Inventory | None:
    """
    Get details for a particular inventory item.

    :param inventory_id: The ID of the inventory item to retrieve
    :type inventory_id: int
    :return: The inventory item with the specified ID, or None if not found
    :rtype: Inventory | None
    """

    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/inventory/{inventory_id}"
    response = http_get(url=url, title="Inventory Return")

    if "inventory" in response.json():
        return Inventory(**response.json()["inventory"])
    else:
        return None


@Decorators.check_env_vars
def inventories_return(filter: dict | None = None) -> list[Inventory]:
    """
    Returns all inventory items.

    :param filter: A dictionary of fields and their values to filter the inventory items by
    :type filter: dict, optional
    :return: A list of all inventory items matching the filter
    :rtype: list[Inventory]
    """

    if filter:
        for field in filter:
            if field not in Inventory.model_fields:
                raise ValueError(f"'{field}' is not a valid field for an inventory.")
        filter = {"filters": filter}
    else:
        filter = None

    url = (
        f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/inventory"
    )

    all_inventories = []

    while True:
        response = http_get(url=url, payload=filter, title="Inventories Return")
        data = response.json()

        if "inventory" not in data:
            logger.error(f"Error, could not get inventories: {response.content}")
            raise Exception(f"Error, could not get inventories: {response.content}")

        all_inventories.extend(data["inventory"])

        if (
            "metadata" not in data
            or "next_page" not in data["metadata"]
            or data["metadata"]["next_page"] is None
        ):
            break

        # Get the next page's url from the current page of data.
        url = data["metadata"]["next_page"]

        time.sleep(1)

    return [Inventory(**x) for x in all_inventories]


@Decorators.check_env_vars
def inventories_search(search_term: str) -> list[Inventory]:
    """
    Searches for inventory items. Largely equivalent to the search box in the EZO UI.
    Generally recommended to use inventories_return with a filter if you have any
    sort of specific criteria to go off of. But search can be useful
    for more general queries based off user input.

    :param search_term: The term to search for in inventory items
    :type search_term: str
    :return: A list of inventory items matching the search term
    :rtype: list[Inventory]
    """

    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/inventory/search"

    all_inventories = []

    while True:
        response = http_get(
            url=url, payload={"search": search_term}, title="Inventories Search"
        )
        data = response.json()

        if "inventories" not in data:
            logger.error(f"Error, could not get inventories: {response.content}")
            raise Exception(f"Error, could not get inventories: {response.content}")

        all_inventories.extend(data["inventories"])

        if (
            "metadata" not in data
            or "next_page" not in data["metadata"]
            or data["metadata"]["next_page"] is None
        ):
            break

        # Get the next page's url from the current page of data.
        url = data["metadata"]["next_page"]

        time.sleep(1)

    return [Inventory(**x) for x in all_inventories]


@Decorators.check_env_vars
def inventory_add_stock(
    inventory_id: int,
    location_id: int,
    quantity: int,
    total_price: float,
    purchased_on: datetime | None = None,
    order_by_id: int | None = None,
    vendor_id: int | None = None,
    comments: str | None = None,
    custom_fields: list[dict] | None = None,
) -> Inventory | None:
    """
    Adds stock to an inventory item at a specific location.

    :param inventory_id: The ID of the inventory item to add stock to
    :type inventory_id: int
    :param location_id: The ID of the location where the stock is being added
    :type location_id: int
    :param quantity: The quantity of stock to add
    :type quantity: int
    :param total_price: The total price of the stock being added
    :type total_price: float
    :param purchased_on: The date the stock was purchased
    :type purchased_on: datetime, optional
    :param order_by_id: The ID of the user who ordered the stock
    :type order_by_id: int, optional
    :param vendor_id: The ID of the vendor from whom the stock was purchased
    :type vendor_id: int, optional
    :param comments: Any comments regarding the stock addition
    :type comments: str, optional
    :param custom_fields: A list of custom fields to associate with the stock addition
    :type custom_fields: list of dict, optional
    :return: The updated inventory item, or None if the addition failed
    :rtype: Inventory | None
    """

    params = {k: v for k, v in locals().items() if v is not None}
    params.pop("inventory_id", None)

    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/inventory/{inventory_id}/add_stock"
    response = http_post(
        url=url, payload={"inventory": params}, title="Inventory Add Stock"
    )

    if response.status_code == 200 and "inventory" in response.json():
        return Inventory(**response.json()["inventory"])
    else:
        return None


@Decorators.check_env_vars
def inventory_remove_stock(
    inventory_id: int,
    location_id: int,
    to_location_id: int,
    quantity: int,
    total_price: float,
    purchased_on: datetime | None = None,
    order_by_id: int | None = None,
    vendor_id: int | None = None,
    comments: str | None = None,
    ignore_conflicting_reservations: bool | None = None,
    custom_fields: list[dict] | None = None,
) -> Inventory | None:
    """
    Removes stock of inventory item at a specific location.

    :param inventory_id: The ID of the inventory item to remove stock from
    :type inventory_id: int
    :param location_id: The ID of the location from which the stock is being removed
    :type location_id: int
    :param to_location_id: The ID of the location to which the stock is being moved (if applicable)
    :type to_location_id: int | None
    :param quantity: The quantity of stock to remove
    :type quantity: int
    :param total_price: The total price of the stock being removed
    :type total_price: float
    :param purchased_on: The date the stock was purchased
    :type purchased_on: datetime, optional
    :param order_by_id: The ID of the user who ordered the stock
    :type order_by_id: int, optional
    :param vendor_id: The ID of the vendor from whom the stock was purchased
    :type vendor_id: int, optional
    :param comments: Any comments regarding the stock removal
    :type comments: str, optional
    :param ignore_conflicting_reservations: Whether to ignore conflicting reservations when removing stock
    :type ignore_conflicting_reservations: bool, optional
    :param custom_fields: A list of custom fields to associate with the stock removal
    :type custom_fields: list of dict, optional
    :return: The updated inventory item, or None if the removal failed
    :rtype: Inventory | None
    """

    params = {k: v for k, v in locals().items() if v is not None}
    params.pop("inventory_id", None)

    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/inventory/{inventory_id}/remove_stock"
    response = http_post(
        url=url, payload={"inventory": params}, title="Inventory Remove Stock"
    )

    if response.status_code == 200 and "inventory" in response.json():
        return Inventory(**response.json()["inventory"])
    else:
        return None


@Decorators.check_env_vars
def inventory_update_location(inventory_id: int, location_id: int) -> Inventory | None:
    """
    Updates default location of inventory item.

    :param inventory_id: The ID of the inventory item to update
    :type inventory_id: int
    :param location_id: The ID of the new default location for the inventory item
    :type location_id: int
    :return: The updated inventory item, or None if the update failed
    :rtype: Inventory | None
    """

    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/inventory/{inventory_id}/update_location"
    response = http_patch(
        url=url,
        payload={"inventory": {"location_id": location_id}},
        title="Inventory Update Location",
    )

    if response.status_code == 200 and "inventory" in response.json():
        return Inventory(**response.json()["inventory"])
    else:
        return None


@Decorators.check_env_vars
def inventory_transfer_stock(
    inventory_id: int,
    from_location_id: int,
    to_location_id: int,
    quantity: int,
    total_price: float,
    comments: str | None = None,
    custom_fields: list[dict] | None = None,
):
    """
    Transfers inventory item amount from one location to another.

    :param inventory_id: The ID of the inventory item to transfer stock for
    :type inventory_id: int
    :param from_location_id: The ID of the location from which the stock is being transferred
    :type from_location_id: int
    :param to_location_id: The ID of the location to which the stock is being transferred
    :type to_location_id: int
    :param quantity: The quantity of stock to transfer
    :type quantity: int
    :param total_price: The total price of the stock being transferred
    :type total_price: float
    :param comments: Any comments regarding the stock transfer
    :type comments: str, optional
    :param custom_fields: A list of custom fields to associate with the stock transfer
    :type custom_fields: list of dict, optional
    :return: The updated inventory item, or None if the transfer failed
    :rtype: Inventory | None
    """

    params = {k: v for k, v in locals().items() if v is not None}
    params.pop("inventory_id", None)

    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/inventory/{inventory_id}/transfer_stock"
    response = http_post(
        url=url, payload={"inventory": params}, title="Inventory Transfer Stock"
    )

    if response.status_code == 200 and "inventory" in response.json():
        return Inventory(**response.json()["inventory"])
    else:
        return None


@Decorators.check_env_vars
def inventory_retire(
    inventory_id: int,
    retire_reason_id: int,
    salvage_value: float | None = None,
    retire_comments: str | None = None,
    location_id: int | None = None,
):
    """
    Retires an inventory item.

    :param inventory_id: The ID of the inventory item to retire
    :type inventory_id: int
    :param retire_reason_id: The ID of the reason for retiring the inventory item
    :type retire_reason_id: int
    :param salvage_value: The salvage value of the inventory item
    :type salvage_value: float, optional
    :param retire_comments: Any comments regarding the retirement of the inventory item
    :type retire_comments: str, optional
    :param location_id: The ID of the location from which the inventory item is being retired
    :type location_id: int, optional
    :return: The updated inventory item, or None if the retirement failed
    :rtype: Inventory | None
    """

    params = {k: v for k, v in locals().items() if v is not None}
    params.pop("inventory_id", None)

    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/inventory/{inventory_id}/retire"
    response = http_put(
        url=url, payload={"inventory": params}, title="Inventory Retire"
    )

    if response.status_code == 200 and "inventory" in response.json():
        return Inventory(**response.json()["inventory"])
    else:
        return None


@Decorators.check_env_vars
def inventory_activate(inventory_id: int):
    """
    Reactivates a retired inventory item.

    :param inventory_id: The ID of the inventory item to reactivate
    :type inventory_id: int
    :return: The updated inventory item, or None if the reactivation failed
    :rtype: Inventory | None
    """

    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/inventory/{inventory_id}/activate"
    response = http_put(url=url, title="Inventory Activate")

    if response.status_code == 200 and "inventory" in response.json():
        return Inventory(**response.json()["inventory"])
    else:
        return None


@Decorators.check_env_vars
def inventory_delete(inventory_id: int):
    """
    Deletes a particular inventory item.

    :param inventory_id: The ID of the inventory item to delete
    :type inventory_id: int
    :return: The deleted inventory item, or None if the deletion failed
    :rtype: Inventory | None
    """

    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/inventory/{inventory_id}"
    response = http_delete(url=url, title="Inventory Delete")

    if response.status_code == 200 and "inventory" in response.json():
        return Inventory(**response.json()["inventory"])
    else:
        return None


@Decorators.check_env_vars
def inventory_quantity_by_location_return(
    inventory_id: int, location_id: int
) -> int | None:
    """
    Gets the current quantity of an inventory item in a particular location.

    :param inventory_id: The ID of the inventory item to check
    :type inventory_id: int
    :param location_id: The ID of the location to check
    :type location_id: int
    :return: The quantity of the inventory item in the specified location, or None if not found
    :rtype: int | None
    """
    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/inventory/{inventory_id}/get_quantity_by_location"
    response = http_get(
        url=url,
        payload={"location_id": location_id},
        title="Inventory Qty by Location Return",
    )

    if response.status_code != 200 or "quantity" not in response.json():
        return None

    return response.json()["quantity"]


# @Decorators.check_env_vars
# def inventory_line_item_locations_return(inventory_id: int):
#     """
#     TODO Doesn't seem to return useful info when testing this endpoint.
#     Just returns a listing of all locations, not anything specific to the
#     particular item.
#     """
#     pass


@Decorators.check_env_vars
def inventory_custom_field_history_return(
    inventory_id: int, custom_field_id: int
) -> list[CustomFieldHistoryItem]:
    """
    Returns custom attribute history for a particulary inventory item.

    :param inventory_id: The ID of the inventory item to retrieve custom field history for
    :type inventory_id: int
    :param custom_field_id: The ID of the custom field to retrieve history for
    :type custom_field_id: int
    :return: A list of custom field history items for the specified inventory item and custom field
    :rtype: list[CustomFieldHistoryItem]
    """

    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/inventory/{inventory_id}/custom_field_history/{custom_field_id}"

    all_custom_history = []

    while True:
        response = http_get(url=url, title="Inventory Custom Field History Return")
        data = response.json()

        if "custom_field" not in data:
            logger.error(
                f"Error, could not get custom attribute history: {response.content}"
            )
            raise Exception(
                f"Error, could not get custom attribute history: {response.content}"
            )

        all_custom_history.extend(data["custom_field"])

        if (
            "metadata" not in data
            or "next_page" not in data["metadata"]
            or data["metadata"]["next_page"] is None
        ):
            break

        # Get the next page's url from the current page of data.
        url = data["metadata"]["next_page"]

        time.sleep(1)

    return [CustomFieldHistoryItem(**x) for x in all_custom_history]


# @Decorators.check_env_vars
# def inventory_location_based_threshold_return():
#     """
#     TODO Doesn't seem to exist. Just getting a 404 when testing in Postman
#     """
#     pass


@Decorators.check_env_vars
def inventory_history_return(inventory_id: int) -> list[StockHistoryItem]:
    """
    Gets stock history of an inventory item.

    :param inventory_id: The ID of the inventory item to retrieve stock history for
    :type inventory_id: int
    :return: A list of stock history items for the specified inventory item
    :rtype: list[StockHistoryItem]
    """
    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/inventory/{inventory_id}/history"

    all_stock_history = []

    while True:
        response = http_get(
            url=url,
            title="Inventory History Return",
        )
        data = response.json()

        if "stock_history" not in data:
            logger.error(f"Error, could not get stock history: {response.content}")
            raise Exception(f"Error, could not get stock history: {response.content}")

        all_stock_history.extend(data["stock_history"])

        if (
            "metadata" not in data
            or "next_page" not in data["metadata"]
            or data["metadata"]["next_page"] is None
        ):
            break

        # Get the next page's url from the current page of data.
        url = data["metadata"]["next_page"]

        time.sleep(1)

    return [StockHistoryItem(**x) for x in all_stock_history]


@Decorators.check_env_vars
def inventory_reservations_return(inventory_id: int) -> list[Reservation]:
    """
    Returns all reservations on an inventory item.

    :param inventory_id: The ID of the inventory item to retrieve reservations for
    :type inventory_id: int
    :return: A list of reservations for the specified inventory item
    :rtype: list[Reservation]
    """

    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/inventory/{inventory_id}/reservations"

    all_reservations = []

    while True:
        response = http_get(
            url=url,
            title="Inventory Reservations Return",
        )
        data = response.json()

        if "reservations" not in data:
            logger.error(f"Error, could not get reservations: {response.content}")
            raise Exception(f"Error, could not get reservations: {response.content}")

        all_reservations.extend(data["reservations"])

        if (
            "metadata" not in data
            or "next_page" not in data["metadata"]
            or data["metadata"]["next_page"] is None
        ):
            break

        # Get the next page's url from the current page of data.
        url = data["metadata"]["next_page"]

        time.sleep(1)

    return [Reservation(**x) for x in all_reservations]


@Decorators.check_env_vars
def inventory_link_to_project(
    project_id: int, inventory_ids: list[int]
) -> ResponseMessages | None:
    """
    Links one or more inventory items to a project.

    :param project_id: ID of the project to link the inventory items to
    :type project_id: int
    :param inventory_ids: List of inventory item IDs to link to the project
    :type inventory_ids: list of int
    :return: Response messages if the linking was successful, or None if it failed
    :rtype: ResponseMessages | None
    """
    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/inventory/link_to_project"
    response = http_post(
        url=url,
        payload={"project_id": project_id, "ids": inventory_ids},
        title="Inventory Link to Project",
    )

    if response.status_code == 200 and "messages" in response.json():
        return ResponseMessages(**response.json()["messages"])
    else:
        return None


@Decorators.check_env_vars
def inventory_unlink_from_project(project_id: int, inventory_ids: list[int]):
    """
    Unlink one or more inventory items from a project.

    :param project_id: ID of the project to unlink the inventory items from
    :type project_id: int
    :param inventory_ids: List of inventory item IDs to unlink from the project
    :type inventory_ids: list of int
    :return: Response messages if the unlinking was successful, or None if it failed
    :rtype: ResponseMessages | None
    """
    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/inventory/unlink_from_project"
    response = http_post(
        url=url,
        payload={"project_id": project_id, "ids": inventory_ids},
        title="Inventory UnLink from Project",
    )

    if response.status_code == 200 and "messages" in response.json(0):
        return ResponseMessages(**response.json()["messages"])
    else:
        return None

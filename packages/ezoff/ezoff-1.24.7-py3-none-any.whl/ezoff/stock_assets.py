import logging
import os
import time

from ezoff._auth import Decorators
from ezoff._helpers import http_post, http_put, http_get, http_patch, http_delete
from ezoff.data_model import ResponseMessages, StockAsset

logger = logging.getLogger(__name__)


@Decorators.check_env_vars
def stock_asset_create(
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
    inventory_threshold: int | None = None,
    default_low_location_threshold: int | None = None,
    default_excess_location_threshold: int | None = None,
    initial_stock_quantity: int | None = None,
    line_item_attributes: list[dict] | None = None,
    location_thresholds_attributes: list[dict] | None = None,
    asset_detail_attributes: dict | None = None,
    custom_fields: list[dict] | None = None,
) -> StockAsset | None:
    """
    Creates a stock asset.

    :param name: Name of the stock asset.
    :type name: str
    :param group_id: ID of the group the stock asset belongs to.
    :type group_id: int
    :param location_id: ID of the location where the stock asset is stored.
    :type location_id: int
    :param display_image: URL of the display image for the stock asset.
    :type display_image: str, optional
    :param identifier: Identifier for the stock asset.
    :type identifier: str, optional
    :param description: Description of the stock asset.
    :type description: str, optional
    :param product_model_number: Product model number of the stock asset.
    :type product_model_number: str, optional
    :param cost_price: Cost price of the stock asset.
    :type cost_price: float, optional
    :param vendor_id: ID of the vendor for the stock asset.
    :type vendor_id: int, optional
    :param salvage_value: Salvage value of the stock asset.
    :type salvage_value: float, optional
    :param sub_group_id: ID of the sub-group the stock asset belongs to.
    :type sub_group_id: int, optional
    :param inventory_threshold: Inventory threshold for the stock asset.
    :type inventory_threshold: int, optional
    :param default_low_location_threshold: Default low location threshold for the stock asset.
    :type default_low_location_threshold: int, optional
    :param default_excess_location_threshold: Default excess location threshold for the stock asset.
    :type default_excess_location_threshold: int, optional
    :param initial_stock_quantity: Initial stock quantity of the stock asset.
    :type initial_stock_quantity: int, optional
    :param line_item_attributes: Line item attributes for the stock asset.
    :type line_item_attributes: list of dict, optional
    :param location_thresholds_attributes: Location thresholds attributes for the stock asset.
    :type location_thresholds_attributes: list of dict, optional
    :param asset_detail_attributes: Asset detail attributes for the stock asset.
    :type asset_detail_attributes: dict, optional
    :param custom_fields: Custom fields for the stock asset.
    :type custom_fields: list of dict, optional
    :return: The created stock asset or None if creation failed.
    :rtype: StockAsset | None
    """

    params = {k: v for k, v in locals().items() if v is not None}

    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/stock_assets"
    response = http_post(
        url=url, payload={"asset_stock": params}, title="Stock Asset Create"
    )

    if response.status_code == 200 and "asset_stock" in response.json(0):
        return StockAsset(**response.json()["asset_stock"])
    else:
        return None


@Decorators.check_env_vars
def stock_asset_return(stock_asset_id: int) -> StockAsset | None:
    """
    Returns a particular stock asset.

    :param stock_asset_id: ID of the stock asset to return.
    :type stock_asset_id: int
    :return: The requested stock asset or None if not found.
    :rtype: StockAsset | None
    """

    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/stock_assets/{stock_asset_id}"
    response = http_get(url=url, title="Stock Asset Return")

    if response.status_code == 200 and "asset_stock":
        return StockAsset(**response.json()["asset_stock"])
    else:
        return None


@Decorators.check_env_vars
def stock_assets_return(filter: dict | None = None) -> list[StockAsset]:
    """
    Returns all stock assets. Optionally, filter using one or more fields.

    :param filter: Dictionary of stock asset fields and the values to filter results by.
    :type filter: dict, optional
    :return: List of StockAsset objects.
    :rtype: list[StockAsset]
    """

    if filter:
        for field in filter:
            if field not in StockAsset.model_fields:
                raise ValueError(f"'{field}' is not a valid field for an inventory.")
        filter = {"filters": filter}
    else:
        filter = None

    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/stock_assets"

    all_stock_assets = []

    while True:
        response = http_get(url=url, payload=filter, title="Stock Assets Return")
        data = response.json()

        if "asset_stock" not in data:
            logger.error(f"Error, could not get stock assets: {response.content}")
            raise Exception(f"Error, could not get stock assets: {response.content}")

        all_stock_assets.extend(data["asset_stock"])

        if (
            "metadata" not in data
            or "next_page" not in data["metadata"]
            or data["metadata"]["next_page"] is None
        ):
            break

        # Get the next page's url from the current page of data.
        url = data["metadata"]["next_page"]

        time.sleep(1)

    return [StockAsset(**x) for x in all_stock_assets]


@Decorators.check_env_vars
def stock_assets_search(search_term: str) -> list[StockAsset]:
    """
    Search for stock assets using some search term. Equivalent to using the search
    box in the UI. Generally recommended to use stock_assets_return with filters
    instead, if you have some specific criteria to go off of. Otherwise, this can
    also be useful if for example, taking user input to search.

    :param search_term: The term to search for.
    :type search_term: str
    :return: List of StockAsset objects matching the search term.
    :rtype: list[StockAsset]
    """

    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/stock_assets/search"

    all_stock_assets = []

    while True:
        response = http_get(
            url=url, payload={"search": search_term}, title="Stock Assets Search"
        )
        data = response.json()

        if "asset_stock" not in data:
            logger.error(f"Error, could not get stock assets: {response.content}")
            raise Exception(f"Error, could not get stock assets: {response.content}")

        all_stock_assets.extend(data["asset_stock"])

        if (
            "metadata" not in data
            or "next_page" not in data["metadata"]
            or data["metadata"]["next_page"] is None
        ):
            break

        # Get the next page's url from the current page of data.
        url = data["metadata"]["next_page"]

        time.sleep(1)

    return [StockAsset(**x) for x in all_stock_assets]


# TODO Quantity By Location
# TODO Line Item Locations
# TODO Current Checkouts
# TODO Custom Field History
# TODO Location Based Threshold
# TODO History
# TODO Reservations

# TODO Add stock
# TODO Transfer stock
# TODO checkout
# TODO checkin
# TODO update location
# TODO retire
# TODO activate
# TODO create reservation
# TODO Link to project
# TODO Unlink from project


@Decorators.check_env_vars
def stock_asset_delete(stock_asset_id: int) -> ResponseMessages | None:
    """
    Deletes a particular stock asset.

    :param stock_asset_id: ID of the stock asset to delete.
    :type stock_asset_id: int
    :return: ResponseMessages object if there are any messages, else None.
    :rtype: ResponseMessages | None
    """
    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/stock_assets/{stock_asset_id}"
    response = http_delete(url=url, title="Stock Asset Delete")

    if response.status_code == 200 and "messages" in response.json():
        return ResponseMessages(**response.json()["messages"])
    else:
        return None

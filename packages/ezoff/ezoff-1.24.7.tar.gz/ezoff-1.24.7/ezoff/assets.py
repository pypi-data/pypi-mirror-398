"""
Covers everything related to fixed assets in EZOffice
"""

import logging
import os
import time
from datetime import date, datetime

from ezoff._auth import Decorators
from ezoff._helpers import (
    http_post,
    http_put,
    http_get,
    http_patch,
    http_delete,
)
from ezoff.data_model import Asset, AssetHistoryItem, ResponseMessages, TokenInput
from ezoff.exceptions import (
    NoDataReturned,
)

logger = logging.getLogger(__name__)


@Decorators.check_env_vars
def asset_create(
    name: str,
    group_id: int,
    location_id: int,
    sub_group_id: int | None = None,
    purchased_on: datetime | None = None,
    display_image: str | None = None,
    identifier: str | None = None,
    description: str | None = None,
    vendor_id: int | None = None,
    product_model_number: str | None = None,
    cost_price: float | None = None,
    salvage_value: float | None = None,
    arbitration: int | None = None,
    custom_fields: list[dict] | None = None,
) -> Asset | None:
    """
    Creates a new asset.

    :param name: The name of the new asset.
    :type name: str
    :param group_id: The top-level grouping to place the asset in.
    :type group_id: int
    :param location_id: The location ID to place the asset in.
    :type location_id: int
    :param sub_group_id: The sub-grouping to place the asset in.
    :type sub_group_id: int, optional
    :param purchased_on: The date the asset was purchased.
    :type purchased_on: datetime, optional
    :param display_image: URL to an image to use as the asset's display image.
    :type display_image: str, optional
    :param identifier: The asset's identifier, such as a serial number or asset tag.
    :type identifier: str, optional
    :param description: A description of the asset.
    :type description: str, optional
    :param vendor_id: The ID of the vendor the asset was purchased from.
    :type vendor_id: int, optional
    :param product_model_number: The product model number of the asset.
    :type product_model_number: str, optional
    :param cost_price: The cost price of the asset.
    :type cost_price: float, optional
    :param salvage_value: The salvage value of the asset.
    :type salvage_value: float, optional
    :param arbitration: The arbitration period of the asset in months.
    :type arbitration: int, optional
    :param custom_fields: List of custom fields to set on the asset. Each item in
        the list should be a dictionary with 'id' and 'value' keys.
    :type custom_fields: list[dict], optional
    :return: The created asset object if successful, else None.
    :rtype: Asset | None
    """

    params = {k: v for k, v in locals().items() if v is not None}

    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/assets"
    response = http_post(url=url, payload={"asset": params}, title="Asset Create")

    if response.status_code == 200 and "asset" in response.json():
        return Asset(**response.json()["asset"])
    else:
        return None


# TODO Bulk create

# TODO Reservation create


@Decorators.check_env_vars
def asset_return(asset_id: int) -> Asset | None:
    """
    Returns a particular asset.

    :param asset_id: The ID of the asset to return.
    :type asset_id: int
    :return: The asset object if found, else None.
    """

    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/assets/{asset_id}"
    response = http_get(url=url, title="Asset Return")

    if response.status_code == 200 and "asset" in response.json():
        return Asset(**response.json()["asset"])
    else:
        return None


@Decorators.check_env_vars
def assets_return(filter: dict | None = None) -> list[Asset]:
    """
    Get a list of all assets, or use the filter parameter to filter results.

    :param filter:  Dictionary of asset fields and the values to filter results by.
    :type filter: dict, optional
    :return: List of assets
    :rtype: list[Asset]
    """

    if filter:
        for field in filter:
            if field not in Asset.model_fields:
                raise ValueError(f"'{field}' is not a valid field for an asset.")
        filter = {"filters": filter}
    else:
        filter = None

    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/assets"
    headers = {
        "Accept": "application/json",
        "Authorization": "Bearer " + os.environ["EZO_TOKEN"],
        "Cache-Control": "no-cache",
        "Host": f"{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
    }
    all_assets = []

    while True:
        response = http_get(
            url=url, payload=filter, headers=headers, title="Assets Return"
        )
        data = response.json()

        if "assets" not in data:
            raise NoDataReturned(f"No fixed assets found: {response.content}")

        all_assets.extend(data["assets"])

        if (
            "metadata" not in data
            or "next_page" not in data["metadata"]
            or data["metadata"]["next_page"] is None
        ):
            break

        # Get the next page's url from the current page of data.
        url = data["metadata"]["next_page"]

    return [Asset(**x) for x in all_assets]


@Decorators.check_env_vars
def assets_search(search_term: str) -> list[Asset]:
    """
    Search for assets.
    The equivalent of the search bar in the EZO UI.
    May not return all assets that match the search term. Better to use the
    assets_return function with filters if you know what you're looking for.

    :param search_term: The search term to search assets by.
    :type search_term: str
    :return: List of Asset objects matching the search term.
    :rtype: list[Asset]
    """

    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/assets/search"
    all_assets = []

    while True:
        response = http_get(
            url=url, params={"search": search_term}, title="Assets Search"
        )
        data = response.json()

        if "assets" not in data:
            logger.error(f"Error, could not get assets: {response.content}")
            raise Exception(f"Error, could not get assets: {response.content}")

        all_assets.extend(data["assets"])

        if (
            "metadata" not in data
            or "next_page" not in data["metadata"]
            or data["metadata"]["next_page"] is None
        ):
            break

        # Get the next page's url from the current page of data.
        url = data["metadata"]["next_page"]

        time.sleep(1)

    return [Asset(**x) for x in all_assets]


@Decorators.check_env_vars
def asset_public_link_return(asset_id: int) -> str | None:
    """
    Returns the public link for a particular asset.

    Note: not sure if might get more than one link for a given asset. The API
    endpoint 'get_public_links' implies so, but in my testing I've only gotten an individual link
    for a given asset.

    :param asset_id: The ID of the asset to get the public link for.
    :type asset_id: int
    :return: The public link if found, else None.
    :rtype: str | None
    """
    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/assets/{asset_id}/get_public_links"
    response = http_get(url=url, title="Asset Public Link Return")

    if "link" in response.json():
        return response.json()["link"]
    else:
        return None


# TODO Booked dates return

# TODO Reservations return


@Decorators.check_env_vars
def assets_token_input_return(q: str) -> list[TokenInput]:
    """
    This isn't an official endpoint in the EZO API. It's used to populate
    the token input dropdowns in the EZO UI. Was previously used in the
    to get the ID needed to filter work orders by asset, but the v2 API
    support directly filtering work orders by asset ID now. Keeping it here
    for posterity.

    Note: If you use "#{Asset Sequence Num}" as the q search parameter, it should
    only return one result. If you use a more general search term. like searching
    for the name, you may get multiple.

    :param q: The search term to search assets by.
    :type q: str
    :return: List of TokenInput objects matching the search term.
    :rtype: list[TokenInput]
    """

    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/assets/items_for_token_input.json"
    response = http_get(
        url=url, params={"include_id": "true", "q": q}, title="Asset Token Input Return"
    )
    data = response.json()

    return [TokenInput(**x) for x in data]


@Decorators.check_env_vars
def asset_history_return(asset_id: int) -> list[AssetHistoryItem]:
    """
    Returns checkout history for a particular asset.

    :param asset_id: The ID of the asset to get history for.
    :type asset_id: int
    :return: List of AssetHistoryItem objects representing the asset's history.
    :rtype: list[AssetHistoryItem]
    """

    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/assets/{asset_id}/history"

    all_history = []

    while True:
        response = http_get(url=url, title="Asset History Return")
        data = response.json()

        if "history" not in data:
            logger.error(f"Error, could not get history: {response.content}")
            raise Exception(f"Error, could not get history: {response.content}")

        all_history.extend(data["history"])

        if (
            "metadata" not in data
            or "next_page" not in data["metadata"]
            or data["metadata"]["next_page"] is None
        ):
            break

        # Get the next page's url from the current page of data.
        url = data["metadata"]["next_page"]

        time.sleep(1)

    return [AssetHistoryItem(**x) for x in all_history]


@Decorators.check_env_vars
def asset_update(asset_id: int, update_data: dict) -> Asset | None:
    """
    Updates a fixed asset.

    :param asset_id: The ID of the asset to update.
    :type asset_id: int
    :param update_data: Dictionary of fields to update on the asset.
    :type update_data: dict
    :return: The updated asset object if successful, else None.
    :rtype: Asset | None
    """

    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/assets/{asset_id}"
    response = http_patch(url=url, payload=update_data, title="Asset Update")

    if response.status_code == 200 and "asset" in response.json():
        return Asset(**response.json()["asset"])
    else:
        return None


# TODO Bulk update


@Decorators.check_env_vars
def asset_checkin(
    asset_id: int,
    location_id: int,
    comments: str | None = None,
    checkin_date: date | None = None,
    custom_fields: list[dict] | None = None,
) -> ResponseMessages | None:
    """
    Check in an asset to a particular location.

    :param asset_id: The ID of the asset to check in.
    :type asset_id: int
    :param location_id: The ID of the location to check the asset in to.
    :type location_id: int
    :param comments: Comments to add to the check-in.
    :type comments: str, optional
    :param checkin_date: The date to record the check-in as. Defaults to today if not provided.
    :type checkin_date: date, optional
    :param custom_fields: List of custom fields to set on check-in. Each item in
        the list should be a dictionary with 'id' and 'value' keys.
    :type custom_fields: list[dict], optional
    :return: ResponseMessages object if there are any messages, else None.
    :rtype: ResponseMessages | None
    """

    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/assets/{asset_id}/checkin"
    response = http_put(
        url=url,
        payload={
            "asset": {
                "comments": comments,
                "location_id": location_id,
                "checkin_date": checkin_date,
                "custom_fields": custom_fields,
            }
        },
        title="Asset Checkin",
    )

    if "messages" in response.json():
        return ResponseMessages(**response.json()["messages"])
    else:
        return None


@Decorators.check_env_vars
def asset_checkout(
    asset_id: int,
    user_id: int,
    location_id: int,
    request_verification: bool,
    comments: str | None = None,
    checkout_forever: bool | None = None,
    till: datetime | None = None,
    project_id: int | None = None,
    ignore_conflicting_reservations: bool | None = None,
    fulfill_user_conflicting_reservations: bool | None = None,
    custom_fields: list[dict] | None = None,
) -> ResponseMessages | None:
    """
    Check out an asset to a member

    Note: If user is inactive, checkout will return a 200 status code but the
    asset will NOT actually be checked out. Response will contain a message.

    :param asset_id: The ID of the asset to check out.
    :type asset_id: int
    :param user_id: The ID of the user to check the asset out to.
    :type user_id: int
    :param location_id: The ID of the location to check the asset out to.
    :type location_id: int
    :param request_verification: Whether to request verification of the asset after checkout.
    :type request_verification: bool
    :param comments: Comments to add to the checkout.
    :type comments: str, optional
    :param checkout_forever: Whether to check the asset out indefinitely.
        If False, the 'till' parameter must be provided.
    :type checkout_forever: bool, optional
    :param till: The date/time to check the asset back in. Required if checkout_forever is False.
    :type till: datetime, optional
    :param project_id: The ID of the project to associate the checkout with.
    :type project_id: int, optional
    :param ignore_conflicting_reservations: Whether to ignore any conflicting reservations
        for the asset when checking out.
    :type ignore_conflicting_reservations: bool, optional
    :param fulfill_user_conflicting_reservations: Whether to fulfill any conflicting reservations
        for the user when checking out.
    :type fulfill_user_conflicting_reservations: bool, optional
    :param custom_fields: List of custom fields to set on checkout. Each item in
        the list should be a dictionary with 'id' and 'value' keys.
    :type custom_fields: list[dict], optional
    :return: ResponseMessages object if there are any messages, else None.
    """

    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/assets/{asset_id}/checkout"
    payload = {
        "asset": {
            "user_id": user_id,
            "comments": comments,
            "location_id": location_id,
            "request_verification": request_verification,
            "checkout_forever": checkout_forever,
            "till": till,
            "ignore_conflicting_reservations": ignore_conflicting_reservations,
            "fulfill_user_conflicting_reservations": fulfill_user_conflicting_reservations,
            "custom_fields": custom_fields,
        }
    }
    response = http_put(url=url, payload=payload, title="Asset Checkout")

    if "messages" in response.json():
        return ResponseMessages(**response.json()["messages"])
    else:
        return None


@Decorators.check_env_vars
def asset_retire(
    asset_id: int,
    retired_on: datetime,
    retire_reason_id: int,
    salvage_value: float | None = None,
    retire_comments: str | None = None,
    location_id: int | None = None,
) -> Asset | None:
    """
    Retires an asset. Asset needs to be in an available state to retire. Essentially,
    making it no longer active/available for checking out.

    :param asset_id: The ID of the asset to retire.
    :type asset_id: int
    :param retired_on: The date to record the asset as retired.
    :type retired_on: datetime
    :param retire_reason_id: The ID of the reason for retiring the asset.
    :type retire_reason_id: int
    :param salvage_value: The salvage value of the asset.
    :type salvage_value: float, optional
    :param retire_comments: Comments to add to the retirement.
    :type retire_comments: str, optional
    :param location_id: The ID of the location to move the asset to upon retirement.
    :type location_id: int, optional
    :return: The updated asset object with retired status if successful, else None.
    :rtype: Asset | None
    """

    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/assets/{asset_id}/retire"
    payload = {
        "asset": {
            "retired_on": retired_on,
            "retire_reason_id": retire_reason_id,
            "salvage_value": salvage_value,
            "retire_comments": retire_comments,
            "location_id": location_id,
        }
    }
    response = http_put(url=url, payload=payload, title="Asset Retire")

    if "asset" in response.json():
        return Asset(**response.json()["asset"])
    else:
        return None


@Decorators.check_env_vars
def asset_activate(asset_id: int, location_id: int | None = None) -> Asset | None:
    """
    Reactivates a retired asset.

    :param asset_id: The ID of the asset to reactivate.
    :type asset_id: int
    :param location_id: The ID of the location to move the asset to upon reactivation.
        If not provided, asset will remain in its current location.
    :type location_id: int, optional
    :return: The updated asset object with active status if successful, else None.
    :rtype: Asset | None
    """

    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/assets/{asset_id}/activate"
    payload = {"asset": {"location_id": location_id}}
    response = http_put(url=url, payload=payload, title="Asset Activate")

    if "asset" in response.json():
        return Asset(**response.json()["asset"])
    else:
        return None


@Decorators.check_env_vars
def asset_verification_request(asset_id: int, note: str) -> dict:
    """
    Creates a verification request for a particular asset. Prompts the user the
    asset is currently checked out to to verify that they do still have ownership
    of it.

    :param asset_id: The ID of the asset to create a verification request for.
    :type asset_id: int
    :param note: A note to include with the verification request.
    :type note: str
    :return: The response from the API as a dictionary.
    :rtype: dict
    """

    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/assets/{asset_id}/audits.json"
    # Not entirely sure on correct request body. Endpoint not yet documented in EZO v2
    # API, so just copying what I'm seeing in the browser's network tools when doing a verification request
    payload = {
        "asset_id": asset_id,
        "custom_substate_id": "",
        "audit": {
            "custom_required": "1",
            "custom_note": note,
        },
    }
    response = http_post(url=url, payload=payload, title="Asset Verification Request")

    return response.json()


@Decorators.check_env_vars
def asset_delete(asset_id: int) -> ResponseMessages | None:
    """
    Delete a particular asset.

    :param asset_id: The ID of the asset to delete.
    :type asset_id: int
    :return: ResponseMessages object if there are any messages, else None.
    :rtype: ResponseMessages | None
    """

    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/assets/{asset_id}"
    response = http_delete(url=url, title="Asset Delete")

    if "messages" in response.json():
        return ResponseMessages(**response.json()["messages"])
    else:
        return None

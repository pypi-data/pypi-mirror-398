import logging
import os
import time

from ezoff._auth import Decorators
from ezoff._helpers import http_post, http_get
from ezoff.data_model import PurchaseOrder

logger = logging.getLogger(__name__)


@Decorators.check_env_vars
def purchase_order_create(title: str, vendor_id: int) -> PurchaseOrder | None:
    """
    Creates a new purchase order.

    :param title: Title of the purchase order.
    :type title: str
    :param vendor_id: ID of the vendor for the purchase order.
    :type vendor_id: int
    :return: The created purchase order or None if creation failed.
    :rtype: PurchaseOrder | None
    """
    params = {k: v for k, v in locals().items() if v is not None}

    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/purchase_orders"
    response = http_post(
        url=url, payload={"purchase_order": params}, title="Purchase Order Create"
    )

    if response.status_code == 200 and "purchase_order" in response.json():
        return PurchaseOrder(**response.json()["purchase_order"])
    else:
        return None


@Decorators.check_env_vars
def purchase_order_return(purchase_order_id: int) -> PurchaseOrder | None:
    """
    Returns a particular purchase order.

    :param purchase_order_id: ID of the purchase order to return.
    :type purchase_order_id: int
    :return: The requested purchase order or None if not found.
    :rtype: PurchaseOrder | None
    """

    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/purchase_orders/{purchase_order_id}"
    response = http_get(url=url, title="Purchase Order Return")

    if response.status_code == 200 and "purchase_order" in response.json():
        return PurchaseOrder(**response.json()["purchase_order"])
    else:
        return None


@Decorators.check_env_vars
def purchase_orders_return() -> list[PurchaseOrder]:
    """
    Returns all purchase orders.

    :return: A list of all purchase orders.
    :rtype: list[PurchaseOrder]
    """
    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/purchase_orders"

    all_purchase_orders = []

    while True:
        response = http_get(url=url, title="Purchase Orders Return")
        data = response.json()

        if "purchase_orders" not in data:
            logger.error(f"Error, could not get purchase orders: {response.content}")
            raise Exception(f"Error, could not get purchase orders: {response.content}")

        all_purchase_orders.extend(data["purchase_orders"])

        if (
            "metadata" not in data
            or "next_page" not in data["metadata"]
            or data["metadata"]["next_page"] is None
        ):
            break

        # Get the next page's url from the current page of data.
        url = data["metadata"]["next_page"]

        time.sleep(1)

    return [PurchaseOrder(**x) for x in all_purchase_orders]


# TODO Update

# TODO Mark void

# TODO Add items

# TODO Receive items

# TODO Mark Confirmed

# TODO Add items

# TODO Delete

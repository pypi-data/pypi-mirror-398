import logging
import os
import time

from ezoff._helpers import http_get
from ezoff.data_model import RetireReason

logger = logging.getLogger(__name__)


def retire_reasons_return() -> list[RetireReason]:
    """
    Returns all retire reasons.

    :return: A list of all retire reasons.
    :rtype: list[RetireReason]
    """

    url = f"https://{os.environ['EZO_SUBDOMAIN']}.ezofficeinventory.com/api/v2/retire_reasons"

    all_retire_reasons = []

    while True:
        response = http_get(url=url, title="Retire Reasons Return")
        data = response.json()

        if "retire_reasons" not in data:
            logger.error(f"Error, could not get retire reasons: {response.content}")
            raise Exception(f"Error, could not get retire reasons: {response.content}")

        all_retire_reasons.extend(data["retire_reasons"])

        if (
            "metadata" not in data
            or "next_page" not in data["metadata"]
            or data["metadata"]["next_page"] is None
        ):
            break

        # Get the next page's url from the current page of data.
        url = data["metadata"]["next_page"]

        time.sleep(1)

    return [RetireReason(**x) for x in all_retire_reasons]

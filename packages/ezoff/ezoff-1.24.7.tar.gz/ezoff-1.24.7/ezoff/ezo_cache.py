"""
This file contains classes for making cached calls to EZ Office API endpoints.
The parent class EzoCache contains basic caching functionality.
Child classes extend EzoCache and add endpoint specific methods.
"""

import logging
import pickle

from ezoff.assets import asset_return, assets_return
from ezoff.data_model import Asset, Location, Member, WorkOrder
from ezoff.exceptions import (
    AssetNotFound,
    LocationNotFound,
    MemberNotFound,
    WorkOrderNotFound,
)
from ezoff.locations import location_return, locations_return
from ezoff.members import member_return, members_return
from ezoff.work_orders import work_order_return, work_orders_return
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class EzoCache:
    """
    Parent class for caching EZ Office API data.

    :ivar cache: Local cache mapping entry IDs to Pydantic models.
    :ivar cache_id_nums:
    :ivar _debug: Debug mode
    :ivar _use_saved: Whether to use saved pickle files, as opposed to the API.
    :ivar _pickle_file_name: The name of the pickle file to use.
    :ivar _api_call_single: The function to use to retrieve a particular item (using an entry ID).
    :ivar _api_call_multi: The function to use to retrieve multiple items (getting all or optionally using a filter).
    :ivar _data_model: The pydantic model corresponding to the cache class.
    :ivar _not_found_exception: The exception that will be raised if no corresponding entry is found with the API.
    """

    def __init__(self, debug: bool = False, use_saved: bool = False):
        self.cache: dict[int, BaseModel] = {}
        self._debug = debug
        self._use_saved = use_saved
        self._pickle_file_name: str | None = None
        self._api_call_single = None
        self._api_call_single_param_name = "entry_id"
        self._api_call_multi = None
        self._data_model: type[BaseModel] | None = None
        self._not_found_exception: type[Exception] | None = None

    def _get_cache_entry(self, entry_id: int, force_api: bool = False) -> BaseModel:
        """
        Returns BaseModel object representing the entry identified by entry_id.
        Subsequent calls referencing the same entry_id will be retrieved from
        the local cache instead of making further calls to the EZO API.

        :param entry_id: ID of entry to return.
        :param force_api: Wether to get data from the API even if a cached copy exists.
        :raises _not_found_exception: Raised when entry_id is not found.
        :returns BaseModel: Pydantic object.
        """
        if force_api or entry_id not in self.cache:
            params = {self._api_call_single_param_name: entry_id}
            try:
                assert self._api_call_single is not None
                self.cache[entry_id] = self._api_call_single(**params)
                return self.cache[entry_id]

            except self._not_found_exception as e:
                raise self._not_found_exception(
                    f"Entry ID {entry_id} not found. {str(e)}"
                )

        return self.cache[entry_id]

    def clear(self):
        """
        Clears EZO cached data.
        """
        self.cache = {}

    def download(self, filter: dict | None = None) -> None:
        """
        Downloads EZO data into local cache.
        New data is appended to or overwrites locally cached data.

        :param filter: Body/payload filter data for limiting results. See EZ Office API v2 for filter schema.
        """
        logger.info(f"Downloading from EZ Office. Filter: {filter}")

        # Use saved pickle or save a pickle when running in debug mode.
        if self._debug:
            assert self._pickle_file_name is not None
            if self._use_saved:
                with open(self._pickle_file_name, "rb") as f:
                    cache = pickle.load(f)

            else:
                assert self._api_call_multi is not None
                cache = self._api_call_multi(filter=filter)
                with open(self._pickle_file_name, "wb") as f:
                    pickle.dump(cache, f)

        # Call EZO API if not running in debug mode.
        else:
            assert self._api_call_multi is not None
            cache = self._api_call_multi(filter=filter)

        logger.info(f"Returned {len(cache)} results.")
        self.cache = {**self.cache, **{x.id: x for x in cache}}


class AssetCache(EzoCache):
    def __init__(self, debug=False, use_saved=False):
        super().__init__(debug, use_saved)
        self.cache: dict[int, Asset] = {}
        self._pickle_file_name = "ezo_asset_cache.pkl"
        self._api_call_single = asset_return
        self._api_call_single_param_name = "asset_id"
        self._api_call_multi = assets_return
        self._data_model = Asset
        self._not_found_exception = AssetNotFound

    def asset(self, asset_id: int, force_api: bool = False):
        return self._get_cache_entry(entry_id=asset_id, force_api=force_api)

    @property
    def assets(self) -> dict[int, Asset]:
        return self.cache


class LocationCache(EzoCache):
    def __init__(self, debug=False, use_saved=False):
        super().__init__(debug, use_saved)
        self.cache: dict[int, Location] = {}
        self._pickle_file_name = "ezo_location_cache.pkl"
        self._api_call_single = location_return
        self._api_call_single_param_name = "location_id"
        self._api_call_multi = locations_return
        self._data_model = Location
        self._not_found_exception = LocationNotFound

    def location(self, location_id: int, force_api: bool = False):
        return self._get_cache_entry(entry_id=location_id, force_api=force_api)

    @property
    def locations(self) -> dict[int, Location]:
        return self.cache


class MemberCache(EzoCache):
    def __init__(self, debug=False, use_saved=False):
        super().__init__(debug, use_saved)
        self.cache: dict[int, Member] = {}
        self._pickle_file_name = "ezo_member_cache.pkl"
        self._api_call_single = member_return
        self._api_call_single_param_name = "member_id"
        self._api_call_multi = members_return
        self._data_model = Member
        self._not_found_exception = MemberNotFound

    def member(self, member_id: int, force_api: bool = False):
        return self._get_cache_entry(entry_id=member_id, force_api=force_api)

    @property
    def members(self) -> dict[int, Member]:
        return self.cache


class WorkOrderCache(EzoCache):
    def __init__(self, debug=False, use_saved=False):
        super().__init__(debug, use_saved)
        self.cache: dict[int, WorkOrder] = {}
        self._pickle_file_name = "ezo_workorder_cache.pkl"
        self._api_call_single = work_order_return
        self._api_call_single_param_name = "work_order_id"
        self._api_call_multi = work_orders_return
        self._data_model = WorkOrder
        self._not_found_exception = WorkOrderNotFound

    def work_order(self, work_order_id: int, force_api: bool = False):
        return self._get_cache_entry(entry_id=work_order_id, force_api=force_api)

    @property
    def work_orders(self) -> dict[int, WorkOrder]:
        return self.cache

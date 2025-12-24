"""
Module contains any custom exceptions defined for use in package.
"""


class AssetException(Exception):
    """
    Parent class for exceptions related to EZ-Office Fixed Assets.
    """

    def __init__(self, asset_id: str):
        super().__init__("")
        self.asset_id = asset_id


class AssetNotFound(AssetException):
    def __str__(self):
        return f"Asset {self.asset_id} not found in EZ-Office."


class AssetDuplicateIdentificationNumber(Exception):
    pass


class ChecklistLinkError(Exception):
    pass


class ChecklistNotFound(Exception):
    pass


class LocationNotFound(Exception):
    pass


class MemberNotFound(Exception):
    pass


class NoDataReturned(Exception):
    pass


class WorkOrderCompleted(Exception):
    pass


class WorkOrderNotFound(Exception):
    pass


class WorkOrderUpdateError(Exception):
    pass

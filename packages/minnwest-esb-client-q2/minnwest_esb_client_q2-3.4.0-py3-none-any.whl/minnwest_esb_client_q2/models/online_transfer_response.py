from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="OnlineTransferResponse")


@_attrs_define
class OnlineTransferResponse:
    """
    Attributes:
        online_transfer_id (Union[Unset, int]):
    """

    online_transfer_id: Union[Unset, int] = UNSET

    def to_dict(self) -> dict[str, Any]:
        online_transfer_id = self.online_transfer_id

        field_dict: dict[str, Any] = {}
        field_dict.update({})
        if online_transfer_id is not UNSET:
            field_dict["onlineTransferId"] = online_transfer_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        online_transfer_id = d.pop("onlineTransferId", UNSET)

        online_transfer_response = cls(
            online_transfer_id=online_transfer_id,
        )

        return online_transfer_response

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="OnlineUserModModel")


@_attrs_define
class OnlineUserModModel:
    """
    Attributes:
        username (Union[None, str]):
        user_id (Union[None, str]):
        updated_on (Union[Unset, datetime.datetime]):
    """

    username: Union[None, str]
    user_id: Union[None, str]
    updated_on: Union[Unset, datetime.datetime] = UNSET

    def to_dict(self) -> dict[str, Any]:
        username: Union[None, str]
        username = self.username

        user_id: Union[None, str]
        user_id = self.user_id

        updated_on: Union[Unset, str] = UNSET
        if not isinstance(self.updated_on, Unset):
            updated_on = self.updated_on.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "username": username,
                "userId": user_id,
            }
        )
        if updated_on is not UNSET:
            field_dict["updatedOn"] = updated_on

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_username(data: object) -> Union[None, str]:
            if data is None:
                return data
            return cast(Union[None, str], data)

        username = _parse_username(d.pop("username"))

        def _parse_user_id(data: object) -> Union[None, str]:
            if data is None:
                return data
            return cast(Union[None, str], data)

        user_id = _parse_user_id(d.pop("userId"))

        _updated_on = d.pop("updatedOn", UNSET)
        updated_on: Union[Unset, datetime.datetime]
        if isinstance(_updated_on, Unset):
            updated_on = UNSET
        else:
            updated_on = isoparse(_updated_on)

        online_user_mod_model = cls(
            username=username,
            user_id=user_id,
            updated_on=updated_on,
        )

        return online_user_mod_model

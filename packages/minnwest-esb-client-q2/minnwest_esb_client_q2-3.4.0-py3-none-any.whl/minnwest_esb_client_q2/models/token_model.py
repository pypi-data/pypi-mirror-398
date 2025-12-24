import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="TokenModel")


@_attrs_define
class TokenModel:
    """
    Attributes:
        token (Union[None, Unset, str]):
        refresh_token (Union[None, Unset, str]):
        expires (Union[None, Unset, datetime.datetime]):
    """

    token: Union[None, Unset, str] = UNSET
    refresh_token: Union[None, Unset, str] = UNSET
    expires: Union[None, Unset, datetime.datetime] = UNSET

    def to_dict(self) -> dict[str, Any]:
        token: Union[None, Unset, str]
        if isinstance(self.token, Unset):
            token = UNSET
        else:
            token = self.token

        refresh_token: Union[None, Unset, str]
        if isinstance(self.refresh_token, Unset):
            refresh_token = UNSET
        else:
            refresh_token = self.refresh_token

        expires: Union[None, Unset, str]
        if isinstance(self.expires, Unset):
            expires = UNSET
        elif isinstance(self.expires, datetime.datetime):
            expires = self.expires.isoformat()
        else:
            expires = self.expires

        field_dict: dict[str, Any] = {}
        field_dict.update({})
        if token is not UNSET:
            field_dict["token"] = token
        if refresh_token is not UNSET:
            field_dict["refreshToken"] = refresh_token
        if expires is not UNSET:
            field_dict["expires"] = expires

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_token(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        token = _parse_token(d.pop("token", UNSET))

        def _parse_refresh_token(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        refresh_token = _parse_refresh_token(d.pop("refreshToken", UNSET))

        def _parse_expires(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                expires_type_0 = isoparse(data)

                return expires_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        expires = _parse_expires(d.pop("expires", UNSET))

        token_model = cls(
            token=token,
            refresh_token=refresh_token,
            expires=expires,
        )

        return token_model

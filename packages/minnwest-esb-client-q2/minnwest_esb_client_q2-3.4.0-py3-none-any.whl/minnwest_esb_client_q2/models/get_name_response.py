from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="GetNameResponse")


@_attrs_define
class GetNameResponse:
    """
    Attributes:
        name_id (Union[None, Unset, int]):
        user_id (Union[None, Unset, int]):
        emails (Union[None, Unset, list[str]]):
    """

    name_id: Union[None, Unset, int] = UNSET
    user_id: Union[None, Unset, int] = UNSET
    emails: Union[None, Unset, list[str]] = UNSET

    def to_dict(self) -> dict[str, Any]:
        name_id: Union[None, Unset, int]
        if isinstance(self.name_id, Unset):
            name_id = UNSET
        else:
            name_id = self.name_id

        user_id: Union[None, Unset, int]
        if isinstance(self.user_id, Unset):
            user_id = UNSET
        else:
            user_id = self.user_id

        emails: Union[None, Unset, list[str]]
        if isinstance(self.emails, Unset):
            emails = UNSET
        elif isinstance(self.emails, list):
            emails = self.emails

        else:
            emails = self.emails

        field_dict: dict[str, Any] = {}
        field_dict.update({})
        if name_id is not UNSET:
            field_dict["nameId"] = name_id
        if user_id is not UNSET:
            field_dict["userId"] = user_id
        if emails is not UNSET:
            field_dict["emails"] = emails

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_name_id(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        name_id = _parse_name_id(d.pop("nameId", UNSET))

        def _parse_user_id(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        user_id = _parse_user_id(d.pop("userId", UNSET))

        def _parse_emails(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                emails_type_0 = cast(list[str], data)

                return emails_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        emails = _parse_emails(d.pop("emails", UNSET))

        get_name_response = cls(
            name_id=name_id,
            user_id=user_id,
            emails=emails,
        )

        return get_name_response

from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="CustomerPhoneData")


@_attrs_define
class CustomerPhoneData:
    """
    Attributes:
        phone (Union[None, Unset, str]):
        phone_type (Union[None, Unset, str]):
        country_code (Union[None, Unset, int]):
    """

    phone: Union[None, Unset, str] = UNSET
    phone_type: Union[None, Unset, str] = UNSET
    country_code: Union[None, Unset, int] = UNSET

    def to_dict(self) -> dict[str, Any]:
        phone: Union[None, Unset, str]
        if isinstance(self.phone, Unset):
            phone = UNSET
        else:
            phone = self.phone

        phone_type: Union[None, Unset, str]
        if isinstance(self.phone_type, Unset):
            phone_type = UNSET
        else:
            phone_type = self.phone_type

        country_code: Union[None, Unset, int]
        if isinstance(self.country_code, Unset):
            country_code = UNSET
        else:
            country_code = self.country_code

        field_dict: dict[str, Any] = {}
        field_dict.update({})
        if phone is not UNSET:
            field_dict["Phone"] = phone
        if phone_type is not UNSET:
            field_dict["PhoneType"] = phone_type
        if country_code is not UNSET:
            field_dict["CountryCode"] = country_code

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_phone(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        phone = _parse_phone(d.pop("Phone", UNSET))

        def _parse_phone_type(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        phone_type = _parse_phone_type(d.pop("PhoneType", UNSET))

        def _parse_country_code(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        country_code = _parse_country_code(d.pop("CountryCode", UNSET))

        customer_phone_data = cls(
            phone=phone,
            phone_type=phone_type,
            country_code=country_code,
        )

        return customer_phone_data

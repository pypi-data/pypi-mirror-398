from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="CustomerAddress")


@_attrs_define
class CustomerAddress:
    """
    Attributes:
        address_1 (Union[None, Unset, str]):
        address_2 (Union[None, Unset, str]):
        city (Union[None, Unset, str]):
        state (Union[None, Unset, str]):
        zip_ (Union[None, Unset, str]):
        address_type (Union[None, Unset, str]):
        country_code (Union[None, Unset, str]):
    """

    address_1: Union[None, Unset, str] = UNSET
    address_2: Union[None, Unset, str] = UNSET
    city: Union[None, Unset, str] = UNSET
    state: Union[None, Unset, str] = UNSET
    zip_: Union[None, Unset, str] = UNSET
    address_type: Union[None, Unset, str] = UNSET
    country_code: Union[None, Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        address_1: Union[None, Unset, str]
        if isinstance(self.address_1, Unset):
            address_1 = UNSET
        else:
            address_1 = self.address_1

        address_2: Union[None, Unset, str]
        if isinstance(self.address_2, Unset):
            address_2 = UNSET
        else:
            address_2 = self.address_2

        city: Union[None, Unset, str]
        if isinstance(self.city, Unset):
            city = UNSET
        else:
            city = self.city

        state: Union[None, Unset, str]
        if isinstance(self.state, Unset):
            state = UNSET
        else:
            state = self.state

        zip_: Union[None, Unset, str]
        if isinstance(self.zip_, Unset):
            zip_ = UNSET
        else:
            zip_ = self.zip_

        address_type: Union[None, Unset, str]
        if isinstance(self.address_type, Unset):
            address_type = UNSET
        else:
            address_type = self.address_type

        country_code: Union[None, Unset, str]
        if isinstance(self.country_code, Unset):
            country_code = UNSET
        else:
            country_code = self.country_code

        field_dict: dict[str, Any] = {}
        field_dict.update({})
        if address_1 is not UNSET:
            field_dict["Address1"] = address_1
        if address_2 is not UNSET:
            field_dict["Address2"] = address_2
        if city is not UNSET:
            field_dict["City"] = city
        if state is not UNSET:
            field_dict["State"] = state
        if zip_ is not UNSET:
            field_dict["Zip"] = zip_
        if address_type is not UNSET:
            field_dict["AddressType"] = address_type
        if country_code is not UNSET:
            field_dict["CountryCode"] = country_code

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_address_1(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        address_1 = _parse_address_1(d.pop("Address1", UNSET))

        def _parse_address_2(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        address_2 = _parse_address_2(d.pop("Address2", UNSET))

        def _parse_city(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        city = _parse_city(d.pop("City", UNSET))

        def _parse_state(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        state = _parse_state(d.pop("State", UNSET))

        def _parse_zip_(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        zip_ = _parse_zip_(d.pop("Zip", UNSET))

        def _parse_address_type(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        address_type = _parse_address_type(d.pop("AddressType", UNSET))

        def _parse_country_code(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        country_code = _parse_country_code(d.pop("CountryCode", UNSET))

        customer_address = cls(
            address_1=address_1,
            address_2=address_2,
            city=city,
            state=state,
            zip_=zip_,
            address_type=address_type,
            country_code=country_code,
        )

        return customer_address

from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="CustomerContactData")


@_attrs_define
class CustomerContactData:
    """
    Attributes:
        email_address (Union[None, Unset, str]):
    """

    email_address: Union[None, Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        email_address: Union[None, Unset, str]
        if isinstance(self.email_address, Unset):
            email_address = UNSET
        else:
            email_address = self.email_address

        field_dict: dict[str, Any] = {}
        field_dict.update({})
        if email_address is not UNSET:
            field_dict["EmailAddress"] = email_address

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_email_address(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        email_address = _parse_email_address(d.pop("EmailAddress", UNSET))

        customer_contact_data = cls(
            email_address=email_address,
        )

        return customer_contact_data

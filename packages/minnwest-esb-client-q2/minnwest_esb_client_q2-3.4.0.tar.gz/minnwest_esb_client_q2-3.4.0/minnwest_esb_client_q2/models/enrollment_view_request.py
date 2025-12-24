from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="EnrollmentViewRequest")


@_attrs_define
class EnrollmentViewRequest:
    """
    Attributes:
        portfolio (str):
        account_numbers (Union[None, Unset, list[str]]):
        name_id_list (Union[None, Unset, list[str]]):
    """

    portfolio: str
    account_numbers: Union[None, Unset, list[str]] = UNSET
    name_id_list: Union[None, Unset, list[str]] = UNSET

    def to_dict(self) -> dict[str, Any]:
        portfolio = self.portfolio

        account_numbers: Union[None, Unset, list[str]]
        if isinstance(self.account_numbers, Unset):
            account_numbers = UNSET
        elif isinstance(self.account_numbers, list):
            account_numbers = self.account_numbers

        else:
            account_numbers = self.account_numbers

        name_id_list: Union[None, Unset, list[str]]
        if isinstance(self.name_id_list, Unset):
            name_id_list = UNSET
        elif isinstance(self.name_id_list, list):
            name_id_list = self.name_id_list

        else:
            name_id_list = self.name_id_list

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "portfolio": portfolio,
            }
        )
        if account_numbers is not UNSET:
            field_dict["accountNumbers"] = account_numbers
        if name_id_list is not UNSET:
            field_dict["nameIDList"] = name_id_list

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        portfolio = d.pop("portfolio")

        def _parse_account_numbers(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                account_numbers_type_0 = cast(list[str], data)

                return account_numbers_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        account_numbers = _parse_account_numbers(d.pop("accountNumbers", UNSET))

        def _parse_name_id_list(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                name_id_list_type_0 = cast(list[str], data)

                return name_id_list_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        name_id_list = _parse_name_id_list(d.pop("nameIDList", UNSET))

        enrollment_view_request = cls(
            portfolio=portfolio,
            account_numbers=account_numbers,
            name_id_list=name_id_list,
        )

        return enrollment_view_request

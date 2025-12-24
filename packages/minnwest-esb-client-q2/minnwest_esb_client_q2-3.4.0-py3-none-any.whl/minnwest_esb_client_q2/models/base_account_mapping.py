from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..models.account_type import AccountType
from ..types import UNSET, Unset

T = TypeVar("T", bound="BaseAccountMapping")


@_attrs_define
class BaseAccountMapping:
    """
    Attributes:
        account_number (str):
        account_type (AccountType):
        internal_cif (Union[None, Unset, str]):
        external_cif (Union[None, Unset, str]):
        product_id (Union[None, Unset, int]):
        access (Union[None, Unset, int]):
    """

    account_number: str
    account_type: AccountType
    internal_cif: Union[None, Unset, str] = UNSET
    external_cif: Union[None, Unset, str] = UNSET
    product_id: Union[None, Unset, int] = UNSET
    access: Union[None, Unset, int] = UNSET

    def to_dict(self) -> dict[str, Any]:
        account_number = self.account_number

        account_type = self.account_type.value

        internal_cif: Union[None, Unset, str]
        if isinstance(self.internal_cif, Unset):
            internal_cif = UNSET
        else:
            internal_cif = self.internal_cif

        external_cif: Union[None, Unset, str]
        if isinstance(self.external_cif, Unset):
            external_cif = UNSET
        else:
            external_cif = self.external_cif

        product_id: Union[None, Unset, int]
        if isinstance(self.product_id, Unset):
            product_id = UNSET
        else:
            product_id = self.product_id

        access: Union[None, Unset, int]
        if isinstance(self.access, Unset):
            access = UNSET
        else:
            access = self.access

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "accountNumber": account_number,
                "accountType": account_type,
            }
        )
        if internal_cif is not UNSET:
            field_dict["internalCif"] = internal_cif
        if external_cif is not UNSET:
            field_dict["externalCif"] = external_cif
        if product_id is not UNSET:
            field_dict["productId"] = product_id
        if access is not UNSET:
            field_dict["access"] = access

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        account_number = d.pop("accountNumber")

        account_type = AccountType(d.pop("accountType"))

        def _parse_internal_cif(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        internal_cif = _parse_internal_cif(d.pop("internalCif", UNSET))

        def _parse_external_cif(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        external_cif = _parse_external_cif(d.pop("externalCif", UNSET))

        def _parse_product_id(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        product_id = _parse_product_id(d.pop("productId", UNSET))

        def _parse_access(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        access = _parse_access(d.pop("access", UNSET))

        base_account_mapping = cls(
            account_number=account_number,
            account_type=account_type,
            internal_cif=internal_cif,
            external_cif=external_cif,
            product_id=product_id,
            access=access,
        )

        return base_account_mapping

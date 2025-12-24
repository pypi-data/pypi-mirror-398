from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..models.account_application_type import AccountApplicationType
from ..models.account_type import AccountType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.soa_account_additional_properties_type_0 import SoaAccountAdditionalPropertiesType0
    from ..models.soa_transfer import SoaTransfer


T = TypeVar("T", bound="SoaAccount")


@_attrs_define
class SoaAccount:
    """
    Attributes:
        account_number (Union[None, Unset, str]):
        current_balance (Union[Unset, float]):
        account_type (Union[Unset, AccountType]):
        account_application_type (Union[Unset, AccountApplicationType]):
        portfolio (Union[None, Unset, str]):
        transfers (Union[None, Unset, list['SoaTransfer']]):
        additional_properties (Union['SoaAccountAdditionalPropertiesType0', None, Unset]):
    """

    account_number: Union[None, Unset, str] = UNSET
    current_balance: Union[Unset, float] = UNSET
    account_type: Union[Unset, AccountType] = UNSET
    account_application_type: Union[Unset, AccountApplicationType] = UNSET
    portfolio: Union[None, Unset, str] = UNSET
    transfers: Union[None, Unset, list["SoaTransfer"]] = UNSET
    additional_properties: Union["SoaAccountAdditionalPropertiesType0", None, Unset] = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.soa_account_additional_properties_type_0 import SoaAccountAdditionalPropertiesType0

        account_number: Union[None, Unset, str]
        if isinstance(self.account_number, Unset):
            account_number = UNSET
        else:
            account_number = self.account_number

        current_balance = self.current_balance

        account_type: Union[Unset, str] = UNSET
        if not isinstance(self.account_type, Unset):
            account_type = self.account_type.value

        account_application_type: Union[Unset, str] = UNSET
        if not isinstance(self.account_application_type, Unset):
            account_application_type = self.account_application_type.value

        portfolio: Union[None, Unset, str]
        if isinstance(self.portfolio, Unset):
            portfolio = UNSET
        else:
            portfolio = self.portfolio

        transfers: Union[None, Unset, list[dict[str, Any]]]
        if isinstance(self.transfers, Unset):
            transfers = UNSET
        elif isinstance(self.transfers, list):
            transfers = []
            for transfers_type_0_item_data in self.transfers:
                transfers_type_0_item = transfers_type_0_item_data.to_dict()
                transfers.append(transfers_type_0_item)

        else:
            transfers = self.transfers

        additional_properties: Union[None, Unset, dict[str, Any]]
        if isinstance(self.additional_properties, Unset):
            additional_properties = UNSET
        elif isinstance(self.additional_properties, SoaAccountAdditionalPropertiesType0):
            additional_properties = self.additional_properties.to_dict()
        else:
            additional_properties = self.additional_properties

        field_dict: dict[str, Any] = {}
        field_dict.update({})
        if account_number is not UNSET:
            field_dict["accountNumber"] = account_number
        if current_balance is not UNSET:
            field_dict["currentBalance"] = current_balance
        if account_type is not UNSET:
            field_dict["accountType"] = account_type
        if account_application_type is not UNSET:
            field_dict["accountApplicationType"] = account_application_type
        if portfolio is not UNSET:
            field_dict["portfolio"] = portfolio
        if transfers is not UNSET:
            field_dict["transfers"] = transfers
        if additional_properties is not UNSET:
            field_dict["additionalProperties"] = additional_properties

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.soa_account_additional_properties_type_0 import SoaAccountAdditionalPropertiesType0
        from ..models.soa_transfer import SoaTransfer

        d = dict(src_dict)

        def _parse_account_number(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        account_number = _parse_account_number(d.pop("accountNumber", UNSET))

        current_balance = d.pop("currentBalance", UNSET)

        _account_type = d.pop("accountType", UNSET)
        account_type: Union[Unset, AccountType]
        if isinstance(_account_type, Unset):
            account_type = UNSET
        else:
            account_type = AccountType(_account_type)

        _account_application_type = d.pop("accountApplicationType", UNSET)
        account_application_type: Union[Unset, AccountApplicationType]
        if isinstance(_account_application_type, Unset):
            account_application_type = UNSET
        else:
            account_application_type = AccountApplicationType(_account_application_type)

        def _parse_portfolio(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        portfolio = _parse_portfolio(d.pop("portfolio", UNSET))

        def _parse_transfers(data: object) -> Union[None, Unset, list["SoaTransfer"]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                transfers_type_0 = []
                _transfers_type_0 = data
                for transfers_type_0_item_data in _transfers_type_0:
                    transfers_type_0_item = SoaTransfer.from_dict(transfers_type_0_item_data)

                    transfers_type_0.append(transfers_type_0_item)

                return transfers_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list["SoaTransfer"]], data)

        transfers = _parse_transfers(d.pop("transfers", UNSET))

        def _parse_additional_properties(data: object) -> Union["SoaAccountAdditionalPropertiesType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                additional_properties_type_0 = SoaAccountAdditionalPropertiesType0.from_dict(data)

                return additional_properties_type_0
            except:  # noqa: E722
                pass
            return cast(Union["SoaAccountAdditionalPropertiesType0", None, Unset], data)

        additional_properties = _parse_additional_properties(d.pop("additionalProperties", UNSET))

        soa_account = cls(
            account_number=account_number,
            current_balance=current_balance,
            account_type=account_type,
            account_application_type=account_application_type,
            portfolio=portfolio,
            transfers=transfers,
            additional_properties=additional_properties,
        )

        return soa_account

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..models.transfer_frequency import TransferFrequency
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.online_user_mod_model import OnlineUserModModel


T = TypeVar("T", bound="OnlineTransferRequest")


@_attrs_define
class OnlineTransferRequest:
    """
    Attributes:
        user (OnlineUserModModel):
        from_account_number (Union[None, str]):
        to_account_number (Union[None, str]):
        portfolio_name_line (Union[None, str]):
        amount (float):
        frequency (TransferFrequency):
        memo (Union[None, Unset, str]):
    """

    user: "OnlineUserModModel"
    from_account_number: Union[None, str]
    to_account_number: Union[None, str]
    portfolio_name_line: Union[None, str]
    amount: float
    frequency: TransferFrequency
    memo: Union[None, Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        user = self.user.to_dict()

        from_account_number: Union[None, str]
        from_account_number = self.from_account_number

        to_account_number: Union[None, str]
        to_account_number = self.to_account_number

        portfolio_name_line: Union[None, str]
        portfolio_name_line = self.portfolio_name_line

        amount = self.amount

        frequency = self.frequency.value

        memo: Union[None, Unset, str]
        if isinstance(self.memo, Unset):
            memo = UNSET
        else:
            memo = self.memo

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "user": user,
                "fromAccountNumber": from_account_number,
                "toAccountNumber": to_account_number,
                "portfolioNameLine": portfolio_name_line,
                "amount": amount,
                "frequency": frequency,
            }
        )
        if memo is not UNSET:
            field_dict["memo"] = memo

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.online_user_mod_model import OnlineUserModModel

        d = dict(src_dict)
        user = OnlineUserModModel.from_dict(d.pop("user"))

        def _parse_from_account_number(data: object) -> Union[None, str]:
            if data is None:
                return data
            return cast(Union[None, str], data)

        from_account_number = _parse_from_account_number(d.pop("fromAccountNumber"))

        def _parse_to_account_number(data: object) -> Union[None, str]:
            if data is None:
                return data
            return cast(Union[None, str], data)

        to_account_number = _parse_to_account_number(d.pop("toAccountNumber"))

        def _parse_portfolio_name_line(data: object) -> Union[None, str]:
            if data is None:
                return data
            return cast(Union[None, str], data)

        portfolio_name_line = _parse_portfolio_name_line(d.pop("portfolioNameLine"))

        amount = d.pop("amount")

        frequency = TransferFrequency(d.pop("frequency"))

        def _parse_memo(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        memo = _parse_memo(d.pop("memo", UNSET))

        online_transfer_request = cls(
            user=user,
            from_account_number=from_account_number,
            to_account_number=to_account_number,
            portfolio_name_line=portfolio_name_line,
            amount=amount,
            frequency=frequency,
            memo=memo,
        )

        return online_transfer_request

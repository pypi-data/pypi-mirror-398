from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.base_account_mapping import BaseAccountMapping


T = TypeVar("T", bound="PortfolioTransferViewRequest")


@_attrs_define
class PortfolioTransferViewRequest:
    """
    Attributes:
        accounts (list['BaseAccountMapping']):
        portfolio (Union[None, Unset, str]):
        user_id (Union[None, Unset, int]):
        customer_id (Union[None, Unset, int]):
        session_id (Union[None, Unset, str]):
        logon_name (Union[None, Unset, str]):
        is_csr_assist (Union[None, Unset, bool]):
        logon_audit_id (Union[None, Unset, str]):
    """

    accounts: list["BaseAccountMapping"]
    portfolio: Union[None, Unset, str] = UNSET
    user_id: Union[None, Unset, int] = UNSET
    customer_id: Union[None, Unset, int] = UNSET
    session_id: Union[None, Unset, str] = UNSET
    logon_name: Union[None, Unset, str] = UNSET
    is_csr_assist: Union[None, Unset, bool] = UNSET
    logon_audit_id: Union[None, Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        accounts = []
        for accounts_item_data in self.accounts:
            accounts_item = accounts_item_data.to_dict()
            accounts.append(accounts_item)

        portfolio: Union[None, Unset, str]
        if isinstance(self.portfolio, Unset):
            portfolio = UNSET
        else:
            portfolio = self.portfolio

        user_id: Union[None, Unset, int]
        if isinstance(self.user_id, Unset):
            user_id = UNSET
        else:
            user_id = self.user_id

        customer_id: Union[None, Unset, int]
        if isinstance(self.customer_id, Unset):
            customer_id = UNSET
        else:
            customer_id = self.customer_id

        session_id: Union[None, Unset, str]
        if isinstance(self.session_id, Unset):
            session_id = UNSET
        else:
            session_id = self.session_id

        logon_name: Union[None, Unset, str]
        if isinstance(self.logon_name, Unset):
            logon_name = UNSET
        else:
            logon_name = self.logon_name

        is_csr_assist: Union[None, Unset, bool]
        if isinstance(self.is_csr_assist, Unset):
            is_csr_assist = UNSET
        else:
            is_csr_assist = self.is_csr_assist

        logon_audit_id: Union[None, Unset, str]
        if isinstance(self.logon_audit_id, Unset):
            logon_audit_id = UNSET
        else:
            logon_audit_id = self.logon_audit_id

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "accounts": accounts,
            }
        )
        if portfolio is not UNSET:
            field_dict["portfolio"] = portfolio
        if user_id is not UNSET:
            field_dict["userId"] = user_id
        if customer_id is not UNSET:
            field_dict["customerId"] = customer_id
        if session_id is not UNSET:
            field_dict["sessionId"] = session_id
        if logon_name is not UNSET:
            field_dict["logonName"] = logon_name
        if is_csr_assist is not UNSET:
            field_dict["isCsrAssist"] = is_csr_assist
        if logon_audit_id is not UNSET:
            field_dict["logonAuditId"] = logon_audit_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.base_account_mapping import BaseAccountMapping

        d = dict(src_dict)
        accounts = []
        _accounts = d.pop("accounts")
        for accounts_item_data in _accounts:
            accounts_item = BaseAccountMapping.from_dict(accounts_item_data)

            accounts.append(accounts_item)

        def _parse_portfolio(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        portfolio = _parse_portfolio(d.pop("portfolio", UNSET))

        def _parse_user_id(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        user_id = _parse_user_id(d.pop("userId", UNSET))

        def _parse_customer_id(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        customer_id = _parse_customer_id(d.pop("customerId", UNSET))

        def _parse_session_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        session_id = _parse_session_id(d.pop("sessionId", UNSET))

        def _parse_logon_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        logon_name = _parse_logon_name(d.pop("logonName", UNSET))

        def _parse_is_csr_assist(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        is_csr_assist = _parse_is_csr_assist(d.pop("isCsrAssist", UNSET))

        def _parse_logon_audit_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        logon_audit_id = _parse_logon_audit_id(d.pop("logonAuditId", UNSET))

        portfolio_transfer_view_request = cls(
            accounts=accounts,
            portfolio=portfolio,
            user_id=user_id,
            customer_id=customer_id,
            session_id=session_id,
            logon_name=logon_name,
            is_csr_assist=is_csr_assist,
            logon_audit_id=logon_audit_id,
        )

        return portfolio_transfer_view_request

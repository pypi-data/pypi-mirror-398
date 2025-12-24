import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.reward_detail import RewardDetail


T = TypeVar("T", bound="RewardAccountDetails")


@_attrs_define
class RewardAccountDetails:
    """
    Attributes:
        account_number (Union[None, str]):
        portfolio (Union[None, str]):
        cycle_code (Union[None, str]):
        service_charge_message (Union[None, str]):
        product_code (Union[Unset, int]):
        as_of (Union[None, Unset, datetime.datetime]):
        total_earned (Union[Unset, float]):
        max_earn (Union[Unset, float]):
        ytd_earned (Union[Unset, float]):
        debit_cashback_earned (Union[Unset, float]):
        debit_purchases_amount (Union[Unset, float]):
        debit_cashback_percent (Union[Unset, float]):
        debit_cashback_max (Union[Unset, float]):
        atm_fee_refund_earned (Union[Unset, float]):
        max_atm_fee_refund (Union[Unset, float]):
        feature_names (Union[None, Unset, list[str]]):
        service_charge_waived (Union[Unset, bool]):
        enrolled_in_direct_deposit (Union[Unset, bool]):
        enrolled_in_e_statements (Union[Unset, bool]):
        rewards (Union[None, Unset, list['RewardDetail']]):
    """

    account_number: Union[None, str]
    portfolio: Union[None, str]
    cycle_code: Union[None, str]
    service_charge_message: Union[None, str]
    product_code: Union[Unset, int] = UNSET
    as_of: Union[None, Unset, datetime.datetime] = UNSET
    total_earned: Union[Unset, float] = UNSET
    max_earn: Union[Unset, float] = UNSET
    ytd_earned: Union[Unset, float] = UNSET
    debit_cashback_earned: Union[Unset, float] = UNSET
    debit_purchases_amount: Union[Unset, float] = UNSET
    debit_cashback_percent: Union[Unset, float] = UNSET
    debit_cashback_max: Union[Unset, float] = UNSET
    atm_fee_refund_earned: Union[Unset, float] = UNSET
    max_atm_fee_refund: Union[Unset, float] = UNSET
    feature_names: Union[None, Unset, list[str]] = UNSET
    service_charge_waived: Union[Unset, bool] = UNSET
    enrolled_in_direct_deposit: Union[Unset, bool] = UNSET
    enrolled_in_e_statements: Union[Unset, bool] = UNSET
    rewards: Union[None, Unset, list["RewardDetail"]] = UNSET

    def to_dict(self) -> dict[str, Any]:
        account_number: Union[None, str]
        account_number = self.account_number

        portfolio: Union[None, str]
        portfolio = self.portfolio

        cycle_code: Union[None, str]
        cycle_code = self.cycle_code

        service_charge_message: Union[None, str]
        service_charge_message = self.service_charge_message

        product_code = self.product_code

        as_of: Union[None, Unset, str]
        if isinstance(self.as_of, Unset):
            as_of = UNSET
        elif isinstance(self.as_of, datetime.datetime):
            as_of = self.as_of.isoformat()
        else:
            as_of = self.as_of

        total_earned = self.total_earned

        max_earn = self.max_earn

        ytd_earned = self.ytd_earned

        debit_cashback_earned = self.debit_cashback_earned

        debit_purchases_amount = self.debit_purchases_amount

        debit_cashback_percent = self.debit_cashback_percent

        debit_cashback_max = self.debit_cashback_max

        atm_fee_refund_earned = self.atm_fee_refund_earned

        max_atm_fee_refund = self.max_atm_fee_refund

        feature_names: Union[None, Unset, list[str]]
        if isinstance(self.feature_names, Unset):
            feature_names = UNSET
        elif isinstance(self.feature_names, list):
            feature_names = self.feature_names

        else:
            feature_names = self.feature_names

        service_charge_waived = self.service_charge_waived

        enrolled_in_direct_deposit = self.enrolled_in_direct_deposit

        enrolled_in_e_statements = self.enrolled_in_e_statements

        rewards: Union[None, Unset, list[dict[str, Any]]]
        if isinstance(self.rewards, Unset):
            rewards = UNSET
        elif isinstance(self.rewards, list):
            rewards = []
            for rewards_type_0_item_data in self.rewards:
                rewards_type_0_item = rewards_type_0_item_data.to_dict()
                rewards.append(rewards_type_0_item)

        else:
            rewards = self.rewards

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "accountNumber": account_number,
                "portfolio": portfolio,
                "cycleCode": cycle_code,
                "serviceChargeMessage": service_charge_message,
            }
        )
        if product_code is not UNSET:
            field_dict["productCode"] = product_code
        if as_of is not UNSET:
            field_dict["asOf"] = as_of
        if total_earned is not UNSET:
            field_dict["totalEarned"] = total_earned
        if max_earn is not UNSET:
            field_dict["maxEarn"] = max_earn
        if ytd_earned is not UNSET:
            field_dict["ytdEarned"] = ytd_earned
        if debit_cashback_earned is not UNSET:
            field_dict["debitCashbackEarned"] = debit_cashback_earned
        if debit_purchases_amount is not UNSET:
            field_dict["debitPurchasesAmount"] = debit_purchases_amount
        if debit_cashback_percent is not UNSET:
            field_dict["debitCashbackPercent"] = debit_cashback_percent
        if debit_cashback_max is not UNSET:
            field_dict["debitCashbackMax"] = debit_cashback_max
        if atm_fee_refund_earned is not UNSET:
            field_dict["atmFeeRefundEarned"] = atm_fee_refund_earned
        if max_atm_fee_refund is not UNSET:
            field_dict["maxAtmFeeRefund"] = max_atm_fee_refund
        if feature_names is not UNSET:
            field_dict["featureNames"] = feature_names
        if service_charge_waived is not UNSET:
            field_dict["serviceChargeWaived"] = service_charge_waived
        if enrolled_in_direct_deposit is not UNSET:
            field_dict["enrolledInDirectDeposit"] = enrolled_in_direct_deposit
        if enrolled_in_e_statements is not UNSET:
            field_dict["enrolledInEStatements"] = enrolled_in_e_statements
        if rewards is not UNSET:
            field_dict["rewards"] = rewards

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.reward_detail import RewardDetail

        d = dict(src_dict)

        def _parse_account_number(data: object) -> Union[None, str]:
            if data is None:
                return data
            return cast(Union[None, str], data)

        account_number = _parse_account_number(d.pop("accountNumber"))

        def _parse_portfolio(data: object) -> Union[None, str]:
            if data is None:
                return data
            return cast(Union[None, str], data)

        portfolio = _parse_portfolio(d.pop("portfolio"))

        def _parse_cycle_code(data: object) -> Union[None, str]:
            if data is None:
                return data
            return cast(Union[None, str], data)

        cycle_code = _parse_cycle_code(d.pop("cycleCode"))

        def _parse_service_charge_message(data: object) -> Union[None, str]:
            if data is None:
                return data
            return cast(Union[None, str], data)

        service_charge_message = _parse_service_charge_message(d.pop("serviceChargeMessage"))

        product_code = d.pop("productCode", UNSET)

        def _parse_as_of(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                as_of_type_0 = isoparse(data)

                return as_of_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        as_of = _parse_as_of(d.pop("asOf", UNSET))

        total_earned = d.pop("totalEarned", UNSET)

        max_earn = d.pop("maxEarn", UNSET)

        ytd_earned = d.pop("ytdEarned", UNSET)

        debit_cashback_earned = d.pop("debitCashbackEarned", UNSET)

        debit_purchases_amount = d.pop("debitPurchasesAmount", UNSET)

        debit_cashback_percent = d.pop("debitCashbackPercent", UNSET)

        debit_cashback_max = d.pop("debitCashbackMax", UNSET)

        atm_fee_refund_earned = d.pop("atmFeeRefundEarned", UNSET)

        max_atm_fee_refund = d.pop("maxAtmFeeRefund", UNSET)

        def _parse_feature_names(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                feature_names_type_0 = cast(list[str], data)

                return feature_names_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        feature_names = _parse_feature_names(d.pop("featureNames", UNSET))

        service_charge_waived = d.pop("serviceChargeWaived", UNSET)

        enrolled_in_direct_deposit = d.pop("enrolledInDirectDeposit", UNSET)

        enrolled_in_e_statements = d.pop("enrolledInEStatements", UNSET)

        def _parse_rewards(data: object) -> Union[None, Unset, list["RewardDetail"]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                rewards_type_0 = []
                _rewards_type_0 = data
                for rewards_type_0_item_data in _rewards_type_0:
                    rewards_type_0_item = RewardDetail.from_dict(rewards_type_0_item_data)

                    rewards_type_0.append(rewards_type_0_item)

                return rewards_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list["RewardDetail"]], data)

        rewards = _parse_rewards(d.pop("rewards", UNSET))

        reward_account_details = cls(
            account_number=account_number,
            portfolio=portfolio,
            cycle_code=cycle_code,
            service_charge_message=service_charge_message,
            product_code=product_code,
            as_of=as_of,
            total_earned=total_earned,
            max_earn=max_earn,
            ytd_earned=ytd_earned,
            debit_cashback_earned=debit_cashback_earned,
            debit_purchases_amount=debit_purchases_amount,
            debit_cashback_percent=debit_cashback_percent,
            debit_cashback_max=debit_cashback_max,
            atm_fee_refund_earned=atm_fee_refund_earned,
            max_atm_fee_refund=max_atm_fee_refund,
            feature_names=feature_names,
            service_charge_waived=service_charge_waived,
            enrolled_in_direct_deposit=enrolled_in_direct_deposit,
            enrolled_in_e_statements=enrolled_in_e_statements,
            rewards=rewards,
        )

        return reward_account_details

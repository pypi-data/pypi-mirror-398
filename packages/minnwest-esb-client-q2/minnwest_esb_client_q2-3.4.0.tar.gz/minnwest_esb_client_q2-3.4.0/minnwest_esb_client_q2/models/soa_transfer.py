import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..models.account_type import AccountType
from ..models.transfer_credit_type import TransferCreditType
from ..models.transfer_frequency import TransferFrequency
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.soa_transfer_additional_properties_type_0 import SoaTransferAdditionalPropertiesType0


T = TypeVar("T", bound="SoaTransfer")


@_attrs_define
class SoaTransfer:
    """
    Attributes:
        from_account_number (Union[None, Unset, str]):
        to_account_number (Union[None, Unset, str]):
        description (Union[None, Unset, str]):
        remaining_transfers (Union[Unset, int]):
        transfer_frequency_code (Union[None, Unset, int]):
        transfer_frequency (Union[Unset, TransferFrequency]):
        transfer_frequency_description (Union[None, Unset, str]):
        transfer_amount_code (Union[None, Unset, int]):
        next_transfer_date (Union[None, Unset, datetime.datetime]):
        next_transfer_amount (Union[Unset, float]):
        last_transfer_date (Union[None, Unset, datetime.datetime]):
        last_transfer_amount (Union[Unset, float]):
        priority_code (Union[Unset, int]):
        credit_to_type_code (Union[Unset, int]):
        credit_to_type (Union[Unset, TransferCreditType]):
        credit_to_account_type (Union[Unset, AccountType]):
        transfer_day (Union[Unset, int]):
        transfer_cycle_code (Union[Unset, int]):
        cycle_description (Union[None, Unset, str]):
        cycle_frequency (Union[Unset, TransferFrequency]):
        cycle_frequency_description (Union[None, Unset, str]):
        record_id (Union[Unset, int]):
        record_number (Union[Unset, int]):
        expiration_date (Union[None, Unset, datetime.datetime]):
        additional_properties (Union['SoaTransferAdditionalPropertiesType0', None, Unset]):
    """

    from_account_number: Union[None, Unset, str] = UNSET
    to_account_number: Union[None, Unset, str] = UNSET
    description: Union[None, Unset, str] = UNSET
    remaining_transfers: Union[Unset, int] = UNSET
    transfer_frequency_code: Union[None, Unset, int] = UNSET
    transfer_frequency: Union[Unset, TransferFrequency] = UNSET
    transfer_frequency_description: Union[None, Unset, str] = UNSET
    transfer_amount_code: Union[None, Unset, int] = UNSET
    next_transfer_date: Union[None, Unset, datetime.datetime] = UNSET
    next_transfer_amount: Union[Unset, float] = UNSET
    last_transfer_date: Union[None, Unset, datetime.datetime] = UNSET
    last_transfer_amount: Union[Unset, float] = UNSET
    priority_code: Union[Unset, int] = UNSET
    credit_to_type_code: Union[Unset, int] = UNSET
    credit_to_type: Union[Unset, TransferCreditType] = UNSET
    credit_to_account_type: Union[Unset, AccountType] = UNSET
    transfer_day: Union[Unset, int] = UNSET
    transfer_cycle_code: Union[Unset, int] = UNSET
    cycle_description: Union[None, Unset, str] = UNSET
    cycle_frequency: Union[Unset, TransferFrequency] = UNSET
    cycle_frequency_description: Union[None, Unset, str] = UNSET
    record_id: Union[Unset, int] = UNSET
    record_number: Union[Unset, int] = UNSET
    expiration_date: Union[None, Unset, datetime.datetime] = UNSET
    additional_properties: Union["SoaTransferAdditionalPropertiesType0", None, Unset] = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.soa_transfer_additional_properties_type_0 import SoaTransferAdditionalPropertiesType0

        from_account_number: Union[None, Unset, str]
        if isinstance(self.from_account_number, Unset):
            from_account_number = UNSET
        else:
            from_account_number = self.from_account_number

        to_account_number: Union[None, Unset, str]
        if isinstance(self.to_account_number, Unset):
            to_account_number = UNSET
        else:
            to_account_number = self.to_account_number

        description: Union[None, Unset, str]
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        remaining_transfers = self.remaining_transfers

        transfer_frequency_code: Union[None, Unset, int]
        if isinstance(self.transfer_frequency_code, Unset):
            transfer_frequency_code = UNSET
        else:
            transfer_frequency_code = self.transfer_frequency_code

        transfer_frequency: Union[Unset, str] = UNSET
        if not isinstance(self.transfer_frequency, Unset):
            transfer_frequency = self.transfer_frequency.value

        transfer_frequency_description: Union[None, Unset, str]
        if isinstance(self.transfer_frequency_description, Unset):
            transfer_frequency_description = UNSET
        else:
            transfer_frequency_description = self.transfer_frequency_description

        transfer_amount_code: Union[None, Unset, int]
        if isinstance(self.transfer_amount_code, Unset):
            transfer_amount_code = UNSET
        else:
            transfer_amount_code = self.transfer_amount_code

        next_transfer_date: Union[None, Unset, str]
        if isinstance(self.next_transfer_date, Unset):
            next_transfer_date = UNSET
        elif isinstance(self.next_transfer_date, datetime.datetime):
            next_transfer_date = self.next_transfer_date.isoformat()
        else:
            next_transfer_date = self.next_transfer_date

        next_transfer_amount = self.next_transfer_amount

        last_transfer_date: Union[None, Unset, str]
        if isinstance(self.last_transfer_date, Unset):
            last_transfer_date = UNSET
        elif isinstance(self.last_transfer_date, datetime.datetime):
            last_transfer_date = self.last_transfer_date.isoformat()
        else:
            last_transfer_date = self.last_transfer_date

        last_transfer_amount = self.last_transfer_amount

        priority_code = self.priority_code

        credit_to_type_code = self.credit_to_type_code

        credit_to_type: Union[Unset, str] = UNSET
        if not isinstance(self.credit_to_type, Unset):
            credit_to_type = self.credit_to_type.value

        credit_to_account_type: Union[Unset, str] = UNSET
        if not isinstance(self.credit_to_account_type, Unset):
            credit_to_account_type = self.credit_to_account_type.value

        transfer_day = self.transfer_day

        transfer_cycle_code = self.transfer_cycle_code

        cycle_description: Union[None, Unset, str]
        if isinstance(self.cycle_description, Unset):
            cycle_description = UNSET
        else:
            cycle_description = self.cycle_description

        cycle_frequency: Union[Unset, str] = UNSET
        if not isinstance(self.cycle_frequency, Unset):
            cycle_frequency = self.cycle_frequency.value

        cycle_frequency_description: Union[None, Unset, str]
        if isinstance(self.cycle_frequency_description, Unset):
            cycle_frequency_description = UNSET
        else:
            cycle_frequency_description = self.cycle_frequency_description

        record_id = self.record_id

        record_number = self.record_number

        expiration_date: Union[None, Unset, str]
        if isinstance(self.expiration_date, Unset):
            expiration_date = UNSET
        elif isinstance(self.expiration_date, datetime.datetime):
            expiration_date = self.expiration_date.isoformat()
        else:
            expiration_date = self.expiration_date

        additional_properties: Union[None, Unset, dict[str, Any]]
        if isinstance(self.additional_properties, Unset):
            additional_properties = UNSET
        elif isinstance(self.additional_properties, SoaTransferAdditionalPropertiesType0):
            additional_properties = self.additional_properties.to_dict()
        else:
            additional_properties = self.additional_properties

        field_dict: dict[str, Any] = {}
        field_dict.update({})
        if from_account_number is not UNSET:
            field_dict["fromAccountNumber"] = from_account_number
        if to_account_number is not UNSET:
            field_dict["toAccountNumber"] = to_account_number
        if description is not UNSET:
            field_dict["description"] = description
        if remaining_transfers is not UNSET:
            field_dict["remainingTransfers"] = remaining_transfers
        if transfer_frequency_code is not UNSET:
            field_dict["transferFrequencyCode"] = transfer_frequency_code
        if transfer_frequency is not UNSET:
            field_dict["transferFrequency"] = transfer_frequency
        if transfer_frequency_description is not UNSET:
            field_dict["transferFrequencyDescription"] = transfer_frequency_description
        if transfer_amount_code is not UNSET:
            field_dict["transferAmountCode"] = transfer_amount_code
        if next_transfer_date is not UNSET:
            field_dict["nextTransferDate"] = next_transfer_date
        if next_transfer_amount is not UNSET:
            field_dict["nextTransferAmount"] = next_transfer_amount
        if last_transfer_date is not UNSET:
            field_dict["lastTransferDate"] = last_transfer_date
        if last_transfer_amount is not UNSET:
            field_dict["lastTransferAmount"] = last_transfer_amount
        if priority_code is not UNSET:
            field_dict["priorityCode"] = priority_code
        if credit_to_type_code is not UNSET:
            field_dict["creditToTypeCode"] = credit_to_type_code
        if credit_to_type is not UNSET:
            field_dict["creditToType"] = credit_to_type
        if credit_to_account_type is not UNSET:
            field_dict["creditToAccountType"] = credit_to_account_type
        if transfer_day is not UNSET:
            field_dict["transferDay"] = transfer_day
        if transfer_cycle_code is not UNSET:
            field_dict["transferCycleCode"] = transfer_cycle_code
        if cycle_description is not UNSET:
            field_dict["cycleDescription"] = cycle_description
        if cycle_frequency is not UNSET:
            field_dict["cycleFrequency"] = cycle_frequency
        if cycle_frequency_description is not UNSET:
            field_dict["cycleFrequencyDescription"] = cycle_frequency_description
        if record_id is not UNSET:
            field_dict["recordId"] = record_id
        if record_number is not UNSET:
            field_dict["recordNumber"] = record_number
        if expiration_date is not UNSET:
            field_dict["expirationDate"] = expiration_date
        if additional_properties is not UNSET:
            field_dict["additionalProperties"] = additional_properties

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.soa_transfer_additional_properties_type_0 import SoaTransferAdditionalPropertiesType0

        d = dict(src_dict)

        def _parse_from_account_number(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        from_account_number = _parse_from_account_number(d.pop("fromAccountNumber", UNSET))

        def _parse_to_account_number(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        to_account_number = _parse_to_account_number(d.pop("toAccountNumber", UNSET))

        def _parse_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        description = _parse_description(d.pop("description", UNSET))

        remaining_transfers = d.pop("remainingTransfers", UNSET)

        def _parse_transfer_frequency_code(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        transfer_frequency_code = _parse_transfer_frequency_code(d.pop("transferFrequencyCode", UNSET))

        _transfer_frequency = d.pop("transferFrequency", UNSET)
        transfer_frequency: Union[Unset, TransferFrequency]
        if isinstance(_transfer_frequency, Unset):
            transfer_frequency = UNSET
        else:
            transfer_frequency = TransferFrequency(_transfer_frequency)

        def _parse_transfer_frequency_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        transfer_frequency_description = _parse_transfer_frequency_description(
            d.pop("transferFrequencyDescription", UNSET)
        )

        def _parse_transfer_amount_code(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        transfer_amount_code = _parse_transfer_amount_code(d.pop("transferAmountCode", UNSET))

        def _parse_next_transfer_date(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                next_transfer_date_type_0 = isoparse(data)

                return next_transfer_date_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        next_transfer_date = _parse_next_transfer_date(d.pop("nextTransferDate", UNSET))

        next_transfer_amount = d.pop("nextTransferAmount", UNSET)

        def _parse_last_transfer_date(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                last_transfer_date_type_0 = isoparse(data)

                return last_transfer_date_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        last_transfer_date = _parse_last_transfer_date(d.pop("lastTransferDate", UNSET))

        last_transfer_amount = d.pop("lastTransferAmount", UNSET)

        priority_code = d.pop("priorityCode", UNSET)

        credit_to_type_code = d.pop("creditToTypeCode", UNSET)

        _credit_to_type = d.pop("creditToType", UNSET)
        credit_to_type: Union[Unset, TransferCreditType]
        if isinstance(_credit_to_type, Unset):
            credit_to_type = UNSET
        else:
            credit_to_type = TransferCreditType(_credit_to_type)

        _credit_to_account_type = d.pop("creditToAccountType", UNSET)
        credit_to_account_type: Union[Unset, AccountType]
        if isinstance(_credit_to_account_type, Unset):
            credit_to_account_type = UNSET
        else:
            credit_to_account_type = AccountType(_credit_to_account_type)

        transfer_day = d.pop("transferDay", UNSET)

        transfer_cycle_code = d.pop("transferCycleCode", UNSET)

        def _parse_cycle_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        cycle_description = _parse_cycle_description(d.pop("cycleDescription", UNSET))

        _cycle_frequency = d.pop("cycleFrequency", UNSET)
        cycle_frequency: Union[Unset, TransferFrequency]
        if isinstance(_cycle_frequency, Unset):
            cycle_frequency = UNSET
        else:
            cycle_frequency = TransferFrequency(_cycle_frequency)

        def _parse_cycle_frequency_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        cycle_frequency_description = _parse_cycle_frequency_description(d.pop("cycleFrequencyDescription", UNSET))

        record_id = d.pop("recordId", UNSET)

        record_number = d.pop("recordNumber", UNSET)

        def _parse_expiration_date(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                expiration_date_type_0 = isoparse(data)

                return expiration_date_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        expiration_date = _parse_expiration_date(d.pop("expirationDate", UNSET))

        def _parse_additional_properties(data: object) -> Union["SoaTransferAdditionalPropertiesType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                additional_properties_type_0 = SoaTransferAdditionalPropertiesType0.from_dict(data)

                return additional_properties_type_0
            except:  # noqa: E722
                pass
            return cast(Union["SoaTransferAdditionalPropertiesType0", None, Unset], data)

        additional_properties = _parse_additional_properties(d.pop("additionalProperties", UNSET))

        soa_transfer = cls(
            from_account_number=from_account_number,
            to_account_number=to_account_number,
            description=description,
            remaining_transfers=remaining_transfers,
            transfer_frequency_code=transfer_frequency_code,
            transfer_frequency=transfer_frequency,
            transfer_frequency_description=transfer_frequency_description,
            transfer_amount_code=transfer_amount_code,
            next_transfer_date=next_transfer_date,
            next_transfer_amount=next_transfer_amount,
            last_transfer_date=last_transfer_date,
            last_transfer_amount=last_transfer_amount,
            priority_code=priority_code,
            credit_to_type_code=credit_to_type_code,
            credit_to_type=credit_to_type,
            credit_to_account_type=credit_to_account_type,
            transfer_day=transfer_day,
            transfer_cycle_code=transfer_cycle_code,
            cycle_description=cycle_description,
            cycle_frequency=cycle_frequency,
            cycle_frequency_description=cycle_frequency_description,
            record_id=record_id,
            record_number=record_number,
            expiration_date=expiration_date,
            additional_properties=additional_properties,
        )

        return soa_transfer

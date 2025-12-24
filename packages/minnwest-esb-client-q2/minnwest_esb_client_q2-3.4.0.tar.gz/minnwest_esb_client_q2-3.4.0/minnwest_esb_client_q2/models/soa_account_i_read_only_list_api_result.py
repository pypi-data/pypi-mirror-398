from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.soa_account import SoaAccount


T = TypeVar("T", bound="SoaAccountIReadOnlyListApiResult")


@_attrs_define
class SoaAccountIReadOnlyListApiResult:
    """
    Attributes:
        is_success (Union[Unset, bool]):
        correlation_id (Union[None, Unset, str]):
        log_id (Union[None, Unset, int]):
        message (Union[None, Unset, str]):
        data (Union[None, Unset, list['SoaAccount']]):
    """

    is_success: Union[Unset, bool] = UNSET
    correlation_id: Union[None, Unset, str] = UNSET
    log_id: Union[None, Unset, int] = UNSET
    message: Union[None, Unset, str] = UNSET
    data: Union[None, Unset, list["SoaAccount"]] = UNSET

    def to_dict(self) -> dict[str, Any]:
        is_success = self.is_success

        correlation_id: Union[None, Unset, str]
        if isinstance(self.correlation_id, Unset):
            correlation_id = UNSET
        else:
            correlation_id = self.correlation_id

        log_id: Union[None, Unset, int]
        if isinstance(self.log_id, Unset):
            log_id = UNSET
        else:
            log_id = self.log_id

        message: Union[None, Unset, str]
        if isinstance(self.message, Unset):
            message = UNSET
        else:
            message = self.message

        data: Union[None, Unset, list[dict[str, Any]]]
        if isinstance(self.data, Unset):
            data = UNSET
        elif isinstance(self.data, list):
            data = []
            for data_type_0_item_data in self.data:
                data_type_0_item = data_type_0_item_data.to_dict()
                data.append(data_type_0_item)

        else:
            data = self.data

        field_dict: dict[str, Any] = {}
        field_dict.update({})
        if is_success is not UNSET:
            field_dict["isSuccess"] = is_success
        if correlation_id is not UNSET:
            field_dict["correlationId"] = correlation_id
        if log_id is not UNSET:
            field_dict["logId"] = log_id
        if message is not UNSET:
            field_dict["message"] = message
        if data is not UNSET:
            field_dict["data"] = data

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.soa_account import SoaAccount

        d = dict(src_dict)
        is_success = d.pop("isSuccess", UNSET)

        def _parse_correlation_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        correlation_id = _parse_correlation_id(d.pop("correlationId", UNSET))

        def _parse_log_id(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        log_id = _parse_log_id(d.pop("logId", UNSET))

        def _parse_message(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        message = _parse_message(d.pop("message", UNSET))

        def _parse_data(data: object) -> Union[None, Unset, list["SoaAccount"]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                data_type_0 = []
                _data_type_0 = data
                for data_type_0_item_data in _data_type_0:
                    data_type_0_item = SoaAccount.from_dict(data_type_0_item_data)

                    data_type_0.append(data_type_0_item)

                return data_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list["SoaAccount"]], data)

        data = _parse_data(d.pop("data", UNSET))

        soa_account_i_read_only_list_api_result = cls(
            is_success=is_success,
            correlation_id=correlation_id,
            log_id=log_id,
            message=message,
            data=data,
        )

        return soa_account_i_read_only_list_api_result

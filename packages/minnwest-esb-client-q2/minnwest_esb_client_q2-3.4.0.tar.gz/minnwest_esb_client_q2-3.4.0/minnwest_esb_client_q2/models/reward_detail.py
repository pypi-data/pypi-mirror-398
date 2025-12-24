from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.reward_detail_details_type_0 import RewardDetailDetailsType0


T = TypeVar("T", bound="RewardDetail")


@_attrs_define
class RewardDetail:
    """
    Attributes:
        reward_name (Union[None, Unset, str]):
        details (Union['RewardDetailDetailsType0', None, Unset]):
    """

    reward_name: Union[None, Unset, str] = UNSET
    details: Union["RewardDetailDetailsType0", None, Unset] = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.reward_detail_details_type_0 import RewardDetailDetailsType0

        reward_name: Union[None, Unset, str]
        if isinstance(self.reward_name, Unset):
            reward_name = UNSET
        else:
            reward_name = self.reward_name

        details: Union[None, Unset, dict[str, Any]]
        if isinstance(self.details, Unset):
            details = UNSET
        elif isinstance(self.details, RewardDetailDetailsType0):
            details = self.details.to_dict()
        else:
            details = self.details

        field_dict: dict[str, Any] = {}
        field_dict.update({})
        if reward_name is not UNSET:
            field_dict["rewardName"] = reward_name
        if details is not UNSET:
            field_dict["details"] = details

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.reward_detail_details_type_0 import RewardDetailDetailsType0

        d = dict(src_dict)

        def _parse_reward_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        reward_name = _parse_reward_name(d.pop("rewardName", UNSET))

        def _parse_details(data: object) -> Union["RewardDetailDetailsType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                details_type_0 = RewardDetailDetailsType0.from_dict(data)

                return details_type_0
            except:  # noqa: E722
                pass
            return cast(Union["RewardDetailDetailsType0", None, Unset], data)

        details = _parse_details(d.pop("details", UNSET))

        reward_detail = cls(
            reward_name=reward_name,
            details=details,
        )

        return reward_detail

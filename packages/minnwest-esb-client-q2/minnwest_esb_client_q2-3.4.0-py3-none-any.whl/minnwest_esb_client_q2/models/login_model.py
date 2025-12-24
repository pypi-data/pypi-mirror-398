from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

T = TypeVar("T", bound="LoginModel")


@_attrs_define
class LoginModel:
    """
    Attributes:
        user_name (Union[None, str]):
        password (Union[None, str]):
    """

    user_name: Union[None, str]
    password: Union[None, str]

    def to_dict(self) -> dict[str, Any]:
        user_name: Union[None, str]
        user_name = self.user_name

        password: Union[None, str]
        password = self.password

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "userName": user_name,
                "password": password,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_user_name(data: object) -> Union[None, str]:
            if data is None:
                return data
            return cast(Union[None, str], data)

        user_name = _parse_user_name(d.pop("userName"))

        def _parse_password(data: object) -> Union[None, str]:
            if data is None:
                return data
            return cast(Union[None, str], data)

        password = _parse_password(d.pop("password"))

        login_model = cls(
            user_name=user_name,
            password=password,
        )

        return login_model

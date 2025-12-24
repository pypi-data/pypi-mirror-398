from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.application_setting_dto import ApplicationSettingDto


T = TypeVar("T", bound="ApplicationDto")


@_attrs_define
class ApplicationDto:
    """
    Attributes:
        id (Union[Unset, int]):
        name (Union[None, Unset, str]):
        description (Union[None, Unset, str]):
        is_active (Union[Unset, bool]):
        settings (Union[None, Unset, list['ApplicationSettingDto']]):
    """

    id: Union[Unset, int] = UNSET
    name: Union[None, Unset, str] = UNSET
    description: Union[None, Unset, str] = UNSET
    is_active: Union[Unset, bool] = UNSET
    settings: Union[None, Unset, list["ApplicationSettingDto"]] = UNSET

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name: Union[None, Unset, str]
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        description: Union[None, Unset, str]
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        is_active = self.is_active

        settings: Union[None, Unset, list[dict[str, Any]]]
        if isinstance(self.settings, Unset):
            settings = UNSET
        elif isinstance(self.settings, list):
            settings = []
            for settings_type_0_item_data in self.settings:
                settings_type_0_item = settings_type_0_item_data.to_dict()
                settings.append(settings_type_0_item)

        else:
            settings = self.settings

        field_dict: dict[str, Any] = {}
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if name is not UNSET:
            field_dict["name"] = name
        if description is not UNSET:
            field_dict["description"] = description
        if is_active is not UNSET:
            field_dict["isActive"] = is_active
        if settings is not UNSET:
            field_dict["settings"] = settings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.application_setting_dto import ApplicationSettingDto

        d = dict(src_dict)
        id = d.pop("id", UNSET)

        def _parse_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        description = _parse_description(d.pop("description", UNSET))

        is_active = d.pop("isActive", UNSET)

        def _parse_settings(data: object) -> Union[None, Unset, list["ApplicationSettingDto"]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                settings_type_0 = []
                _settings_type_0 = data
                for settings_type_0_item_data in _settings_type_0:
                    settings_type_0_item = ApplicationSettingDto.from_dict(settings_type_0_item_data)

                    settings_type_0.append(settings_type_0_item)

                return settings_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list["ApplicationSettingDto"]], data)

        settings = _parse_settings(d.pop("settings", UNSET))

        application_dto = cls(
            id=id,
            name=name,
            description=description,
            is_active=is_active,
            settings=settings,
        )

        return application_dto

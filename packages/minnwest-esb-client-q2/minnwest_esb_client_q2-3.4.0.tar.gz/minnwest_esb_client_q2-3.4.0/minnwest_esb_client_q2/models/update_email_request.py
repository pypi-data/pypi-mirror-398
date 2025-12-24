from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.update_email_request_extra_type_0 import UpdateEmailRequestExtraType0


T = TypeVar("T", bound="UpdateEmailRequest")


@_attrs_define
class UpdateEmailRequest:
    """
    Attributes:
        name_id (Union[Unset, int]):
        old_email (Union[None, Unset, str]):
        new_email (Union[None, Unset, str]):
        extra (Union['UpdateEmailRequestExtraType0', None, Unset]):
        user_id (Union[None, Unset, int]):
        customer_id (Union[None, Unset, int]):
        session_id (Union[None, Unset, str]):
        logon_name (Union[None, Unset, str]):
        is_csr_assist (Union[None, Unset, bool]):
        logon_audit_id (Union[None, Unset, str]):
    """

    name_id: Union[Unset, int] = UNSET
    old_email: Union[None, Unset, str] = UNSET
    new_email: Union[None, Unset, str] = UNSET
    extra: Union["UpdateEmailRequestExtraType0", None, Unset] = UNSET
    user_id: Union[None, Unset, int] = UNSET
    customer_id: Union[None, Unset, int] = UNSET
    session_id: Union[None, Unset, str] = UNSET
    logon_name: Union[None, Unset, str] = UNSET
    is_csr_assist: Union[None, Unset, bool] = UNSET
    logon_audit_id: Union[None, Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.update_email_request_extra_type_0 import UpdateEmailRequestExtraType0

        name_id = self.name_id

        old_email: Union[None, Unset, str]
        if isinstance(self.old_email, Unset):
            old_email = UNSET
        else:
            old_email = self.old_email

        new_email: Union[None, Unset, str]
        if isinstance(self.new_email, Unset):
            new_email = UNSET
        else:
            new_email = self.new_email

        extra: Union[None, Unset, dict[str, Any]]
        if isinstance(self.extra, Unset):
            extra = UNSET
        elif isinstance(self.extra, UpdateEmailRequestExtraType0):
            extra = self.extra.to_dict()
        else:
            extra = self.extra

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
        field_dict.update({})
        if name_id is not UNSET:
            field_dict["nameId"] = name_id
        if old_email is not UNSET:
            field_dict["oldEmail"] = old_email
        if new_email is not UNSET:
            field_dict["newEmail"] = new_email
        if extra is not UNSET:
            field_dict["extra"] = extra
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
        from ..models.update_email_request_extra_type_0 import UpdateEmailRequestExtraType0

        d = dict(src_dict)
        name_id = d.pop("nameId", UNSET)

        def _parse_old_email(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        old_email = _parse_old_email(d.pop("oldEmail", UNSET))

        def _parse_new_email(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        new_email = _parse_new_email(d.pop("newEmail", UNSET))

        def _parse_extra(data: object) -> Union["UpdateEmailRequestExtraType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                extra_type_0 = UpdateEmailRequestExtraType0.from_dict(data)

                return extra_type_0
            except:  # noqa: E722
                pass
            return cast(Union["UpdateEmailRequestExtraType0", None, Unset], data)

        extra = _parse_extra(d.pop("extra", UNSET))

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

        update_email_request = cls(
            name_id=name_id,
            old_email=old_email,
            new_email=new_email,
            extra=extra,
            user_id=user_id,
            customer_id=customer_id,
            session_id=session_id,
            logon_name=logon_name,
            is_csr_assist=is_csr_assist,
            logon_audit_id=logon_audit_id,
        )

        return update_email_request

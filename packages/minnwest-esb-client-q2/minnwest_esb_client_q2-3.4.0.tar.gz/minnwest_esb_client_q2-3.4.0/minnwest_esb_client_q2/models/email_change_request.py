import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.email_change_request_extra_type_0 import EmailChangeRequestExtraType0


T = TypeVar("T", bound="EmailChangeRequest")


@_attrs_define
class EmailChangeRequest:
    """
    Attributes:
        new_email (str):
        user_id (int):
        name (str):
        requested_at (Union[Unset, datetime.datetime]):
        old_email (Union[None, Unset, str]):
        email_id (Union[None, Unset, int]):
        extra (Union['EmailChangeRequestExtraType0', None, Unset]):
        customer_id (Union[None, Unset, int]):
        session_id (Union[None, Unset, str]):
        logon_name (Union[None, Unset, str]):
        is_csr_assist (Union[None, Unset, bool]):
        logon_audit_id (Union[None, Unset, str]):
    """

    new_email: str
    user_id: int
    name: str
    requested_at: Union[Unset, datetime.datetime] = UNSET
    old_email: Union[None, Unset, str] = UNSET
    email_id: Union[None, Unset, int] = UNSET
    extra: Union["EmailChangeRequestExtraType0", None, Unset] = UNSET
    customer_id: Union[None, Unset, int] = UNSET
    session_id: Union[None, Unset, str] = UNSET
    logon_name: Union[None, Unset, str] = UNSET
    is_csr_assist: Union[None, Unset, bool] = UNSET
    logon_audit_id: Union[None, Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.email_change_request_extra_type_0 import EmailChangeRequestExtraType0

        new_email = self.new_email

        user_id = self.user_id

        name = self.name

        requested_at: Union[Unset, str] = UNSET
        if not isinstance(self.requested_at, Unset):
            requested_at = self.requested_at.isoformat()

        old_email: Union[None, Unset, str]
        if isinstance(self.old_email, Unset):
            old_email = UNSET
        else:
            old_email = self.old_email

        email_id: Union[None, Unset, int]
        if isinstance(self.email_id, Unset):
            email_id = UNSET
        else:
            email_id = self.email_id

        extra: Union[None, Unset, dict[str, Any]]
        if isinstance(self.extra, Unset):
            extra = UNSET
        elif isinstance(self.extra, EmailChangeRequestExtraType0):
            extra = self.extra.to_dict()
        else:
            extra = self.extra

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
                "newEmail": new_email,
                "userId": user_id,
                "name": name,
            }
        )
        if requested_at is not UNSET:
            field_dict["requestedAt"] = requested_at
        if old_email is not UNSET:
            field_dict["oldEmail"] = old_email
        if email_id is not UNSET:
            field_dict["emailId"] = email_id
        if extra is not UNSET:
            field_dict["extra"] = extra
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
        from ..models.email_change_request_extra_type_0 import EmailChangeRequestExtraType0

        d = dict(src_dict)
        new_email = d.pop("newEmail")

        user_id = d.pop("userId")

        name = d.pop("name")

        _requested_at = d.pop("requestedAt", UNSET)
        requested_at: Union[Unset, datetime.datetime]
        if isinstance(_requested_at, Unset):
            requested_at = UNSET
        else:
            requested_at = isoparse(_requested_at)

        def _parse_old_email(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        old_email = _parse_old_email(d.pop("oldEmail", UNSET))

        def _parse_email_id(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        email_id = _parse_email_id(d.pop("emailId", UNSET))

        def _parse_extra(data: object) -> Union["EmailChangeRequestExtraType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                extra_type_0 = EmailChangeRequestExtraType0.from_dict(data)

                return extra_type_0
            except:  # noqa: E722
                pass
            return cast(Union["EmailChangeRequestExtraType0", None, Unset], data)

        extra = _parse_extra(d.pop("extra", UNSET))

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

        email_change_request = cls(
            new_email=new_email,
            user_id=user_id,
            name=name,
            requested_at=requested_at,
            old_email=old_email,
            email_id=email_id,
            extra=extra,
            customer_id=customer_id,
            session_id=session_id,
            logon_name=logon_name,
            is_csr_assist=is_csr_assist,
            logon_audit_id=logon_audit_id,
        )

        return email_change_request

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.get_name_request_extra_type_0 import GetNameRequestExtraType0


T = TypeVar("T", bound="GetNameRequest")


@_attrs_define
class GetNameRequest:
    """
    Attributes:
        customer_name (Union[None, str]):
        customer_tax_id (Union[None, Unset, str]):
        user_ssn (Union[None, Unset, str]):
        user_first_name (Union[None, Unset, str]):
        user_last_name (Union[None, Unset, str]):
        user_middle_name (Union[None, Unset, str]):
        current_email (Union[None, Unset, str]):
        birthday (Union[None, Unset, datetime.date]):
        extra (Union['GetNameRequestExtraType0', None, Unset]):
        user_id (Union[None, Unset, int]):
        customer_id (Union[None, Unset, int]):
        session_id (Union[None, Unset, str]):
        logon_name (Union[None, Unset, str]):
        is_csr_assist (Union[None, Unset, bool]):
        logon_audit_id (Union[None, Unset, str]):
    """

    customer_name: Union[None, str]
    customer_tax_id: Union[None, Unset, str] = UNSET
    user_ssn: Union[None, Unset, str] = UNSET
    user_first_name: Union[None, Unset, str] = UNSET
    user_last_name: Union[None, Unset, str] = UNSET
    user_middle_name: Union[None, Unset, str] = UNSET
    current_email: Union[None, Unset, str] = UNSET
    birthday: Union[None, Unset, datetime.date] = UNSET
    extra: Union["GetNameRequestExtraType0", None, Unset] = UNSET
    user_id: Union[None, Unset, int] = UNSET
    customer_id: Union[None, Unset, int] = UNSET
    session_id: Union[None, Unset, str] = UNSET
    logon_name: Union[None, Unset, str] = UNSET
    is_csr_assist: Union[None, Unset, bool] = UNSET
    logon_audit_id: Union[None, Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.get_name_request_extra_type_0 import GetNameRequestExtraType0

        customer_name: Union[None, str]
        customer_name = self.customer_name

        customer_tax_id: Union[None, Unset, str]
        if isinstance(self.customer_tax_id, Unset):
            customer_tax_id = UNSET
        else:
            customer_tax_id = self.customer_tax_id

        user_ssn: Union[None, Unset, str]
        if isinstance(self.user_ssn, Unset):
            user_ssn = UNSET
        else:
            user_ssn = self.user_ssn

        user_first_name: Union[None, Unset, str]
        if isinstance(self.user_first_name, Unset):
            user_first_name = UNSET
        else:
            user_first_name = self.user_first_name

        user_last_name: Union[None, Unset, str]
        if isinstance(self.user_last_name, Unset):
            user_last_name = UNSET
        else:
            user_last_name = self.user_last_name

        user_middle_name: Union[None, Unset, str]
        if isinstance(self.user_middle_name, Unset):
            user_middle_name = UNSET
        else:
            user_middle_name = self.user_middle_name

        current_email: Union[None, Unset, str]
        if isinstance(self.current_email, Unset):
            current_email = UNSET
        else:
            current_email = self.current_email

        birthday: Union[None, Unset, str]
        if isinstance(self.birthday, Unset):
            birthday = UNSET
        elif isinstance(self.birthday, datetime.date):
            birthday = self.birthday.isoformat()
        else:
            birthday = self.birthday

        extra: Union[None, Unset, dict[str, Any]]
        if isinstance(self.extra, Unset):
            extra = UNSET
        elif isinstance(self.extra, GetNameRequestExtraType0):
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
        field_dict.update(
            {
                "customerName": customer_name,
            }
        )
        if customer_tax_id is not UNSET:
            field_dict["customerTaxId"] = customer_tax_id
        if user_ssn is not UNSET:
            field_dict["userSsn"] = user_ssn
        if user_first_name is not UNSET:
            field_dict["userFirstName"] = user_first_name
        if user_last_name is not UNSET:
            field_dict["userLastName"] = user_last_name
        if user_middle_name is not UNSET:
            field_dict["userMiddleName"] = user_middle_name
        if current_email is not UNSET:
            field_dict["currentEmail"] = current_email
        if birthday is not UNSET:
            field_dict["birthday"] = birthday
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
        from ..models.get_name_request_extra_type_0 import GetNameRequestExtraType0

        d = dict(src_dict)

        def _parse_customer_name(data: object) -> Union[None, str]:
            if data is None:
                return data
            return cast(Union[None, str], data)

        customer_name = _parse_customer_name(d.pop("customerName"))

        def _parse_customer_tax_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        customer_tax_id = _parse_customer_tax_id(d.pop("customerTaxId", UNSET))

        def _parse_user_ssn(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        user_ssn = _parse_user_ssn(d.pop("userSsn", UNSET))

        def _parse_user_first_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        user_first_name = _parse_user_first_name(d.pop("userFirstName", UNSET))

        def _parse_user_last_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        user_last_name = _parse_user_last_name(d.pop("userLastName", UNSET))

        def _parse_user_middle_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        user_middle_name = _parse_user_middle_name(d.pop("userMiddleName", UNSET))

        def _parse_current_email(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        current_email = _parse_current_email(d.pop("currentEmail", UNSET))

        def _parse_birthday(data: object) -> Union[None, Unset, datetime.date]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                birthday_type_0 = isoparse(data).date()

                return birthday_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.date], data)

        birthday = _parse_birthday(d.pop("birthday", UNSET))

        def _parse_extra(data: object) -> Union["GetNameRequestExtraType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                extra_type_0 = GetNameRequestExtraType0.from_dict(data)

                return extra_type_0
            except:  # noqa: E722
                pass
            return cast(Union["GetNameRequestExtraType0", None, Unset], data)

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

        get_name_request = cls(
            customer_name=customer_name,
            customer_tax_id=customer_tax_id,
            user_ssn=user_ssn,
            user_first_name=user_first_name,
            user_last_name=user_last_name,
            user_middle_name=user_middle_name,
            current_email=current_email,
            birthday=birthday,
            extra=extra,
            user_id=user_id,
            customer_id=customer_id,
            session_id=session_id,
            logon_name=logon_name,
            is_csr_assist=is_csr_assist,
            logon_audit_id=logon_audit_id,
        )

        return get_name_request

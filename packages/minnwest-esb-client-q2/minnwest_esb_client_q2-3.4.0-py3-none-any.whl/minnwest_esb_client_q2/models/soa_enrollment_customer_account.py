from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.customer_address import CustomerAddress
    from ..models.customer_contact_data import CustomerContactData
    from ..models.customer_phone_data import CustomerPhoneData
    from ..models.enrollment_account_association import EnrollmentAccountAssociation


T = TypeVar("T", bound="SOAEnrollmentCustomerAccount")


@_attrs_define
class SOAEnrollmentCustomerAccount:
    """
    Attributes:
        name_id (Union[None, Unset, str]):
        customer_type (Union[None, Unset, str]):
        name (Union[None, Unset, str]):
        short_last_name (Union[None, Unset, str]):
        short_first_name (Union[None, Unset, str]):
        middle_initial (Union[None, Unset, str]):
        tax_id_code (Union[None, Unset, str]):
        tax_id_number (Union[None, Unset, int]):
        tax_id_enum_type (Union[None, Unset, str]):
        date_of_birth (Union[None, Unset, str]):
        portfolio_number (Union[None, Unset, str]):
        port_sequence (Union[None, Unset, str]):
        tax_id_type (Union[None, Unset, str]):
        phones (Union[None, Unset, list['CustomerPhoneData']]):
        emails (Union[None, Unset, list['CustomerContactData']]):
        addresses (Union[None, Unset, list['CustomerAddress']]):
        account_associations (Union[None, Unset, list['EnrollmentAccountAssociation']]):
    """

    name_id: Union[None, Unset, str] = UNSET
    customer_type: Union[None, Unset, str] = UNSET
    name: Union[None, Unset, str] = UNSET
    short_last_name: Union[None, Unset, str] = UNSET
    short_first_name: Union[None, Unset, str] = UNSET
    middle_initial: Union[None, Unset, str] = UNSET
    tax_id_code: Union[None, Unset, str] = UNSET
    tax_id_number: Union[None, Unset, int] = UNSET
    tax_id_enum_type: Union[None, Unset, str] = UNSET
    date_of_birth: Union[None, Unset, str] = UNSET
    portfolio_number: Union[None, Unset, str] = UNSET
    port_sequence: Union[None, Unset, str] = UNSET
    tax_id_type: Union[None, Unset, str] = UNSET
    phones: Union[None, Unset, list["CustomerPhoneData"]] = UNSET
    emails: Union[None, Unset, list["CustomerContactData"]] = UNSET
    addresses: Union[None, Unset, list["CustomerAddress"]] = UNSET
    account_associations: Union[None, Unset, list["EnrollmentAccountAssociation"]] = UNSET

    def to_dict(self) -> dict[str, Any]:
        name_id: Union[None, Unset, str]
        if isinstance(self.name_id, Unset):
            name_id = UNSET
        else:
            name_id = self.name_id

        customer_type: Union[None, Unset, str]
        if isinstance(self.customer_type, Unset):
            customer_type = UNSET
        else:
            customer_type = self.customer_type

        name: Union[None, Unset, str]
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        short_last_name: Union[None, Unset, str]
        if isinstance(self.short_last_name, Unset):
            short_last_name = UNSET
        else:
            short_last_name = self.short_last_name

        short_first_name: Union[None, Unset, str]
        if isinstance(self.short_first_name, Unset):
            short_first_name = UNSET
        else:
            short_first_name = self.short_first_name

        middle_initial: Union[None, Unset, str]
        if isinstance(self.middle_initial, Unset):
            middle_initial = UNSET
        else:
            middle_initial = self.middle_initial

        tax_id_code: Union[None, Unset, str]
        if isinstance(self.tax_id_code, Unset):
            tax_id_code = UNSET
        else:
            tax_id_code = self.tax_id_code

        tax_id_number: Union[None, Unset, int]
        if isinstance(self.tax_id_number, Unset):
            tax_id_number = UNSET
        else:
            tax_id_number = self.tax_id_number

        tax_id_enum_type: Union[None, Unset, str]
        if isinstance(self.tax_id_enum_type, Unset):
            tax_id_enum_type = UNSET
        else:
            tax_id_enum_type = self.tax_id_enum_type

        date_of_birth: Union[None, Unset, str]
        if isinstance(self.date_of_birth, Unset):
            date_of_birth = UNSET
        else:
            date_of_birth = self.date_of_birth

        portfolio_number: Union[None, Unset, str]
        if isinstance(self.portfolio_number, Unset):
            portfolio_number = UNSET
        else:
            portfolio_number = self.portfolio_number

        port_sequence: Union[None, Unset, str]
        if isinstance(self.port_sequence, Unset):
            port_sequence = UNSET
        else:
            port_sequence = self.port_sequence

        tax_id_type: Union[None, Unset, str]
        if isinstance(self.tax_id_type, Unset):
            tax_id_type = UNSET
        else:
            tax_id_type = self.tax_id_type

        phones: Union[None, Unset, list[dict[str, Any]]]
        if isinstance(self.phones, Unset):
            phones = UNSET
        elif isinstance(self.phones, list):
            phones = []
            for phones_type_0_item_data in self.phones:
                phones_type_0_item = phones_type_0_item_data.to_dict()
                phones.append(phones_type_0_item)

        else:
            phones = self.phones

        emails: Union[None, Unset, list[dict[str, Any]]]
        if isinstance(self.emails, Unset):
            emails = UNSET
        elif isinstance(self.emails, list):
            emails = []
            for emails_type_0_item_data in self.emails:
                emails_type_0_item = emails_type_0_item_data.to_dict()
                emails.append(emails_type_0_item)

        else:
            emails = self.emails

        addresses: Union[None, Unset, list[dict[str, Any]]]
        if isinstance(self.addresses, Unset):
            addresses = UNSET
        elif isinstance(self.addresses, list):
            addresses = []
            for addresses_type_0_item_data in self.addresses:
                addresses_type_0_item = addresses_type_0_item_data.to_dict()
                addresses.append(addresses_type_0_item)

        else:
            addresses = self.addresses

        account_associations: Union[None, Unset, list[dict[str, Any]]]
        if isinstance(self.account_associations, Unset):
            account_associations = UNSET
        elif isinstance(self.account_associations, list):
            account_associations = []
            for account_associations_type_0_item_data in self.account_associations:
                account_associations_type_0_item = account_associations_type_0_item_data.to_dict()
                account_associations.append(account_associations_type_0_item)

        else:
            account_associations = self.account_associations

        field_dict: dict[str, Any] = {}
        field_dict.update({})
        if name_id is not UNSET:
            field_dict["nameId"] = name_id
        if customer_type is not UNSET:
            field_dict["customerType"] = customer_type
        if name is not UNSET:
            field_dict["name"] = name
        if short_last_name is not UNSET:
            field_dict["shortLastName"] = short_last_name
        if short_first_name is not UNSET:
            field_dict["shortFirstName"] = short_first_name
        if middle_initial is not UNSET:
            field_dict["middleInitial"] = middle_initial
        if tax_id_code is not UNSET:
            field_dict["taxIdCode"] = tax_id_code
        if tax_id_number is not UNSET:
            field_dict["taxIdNumber"] = tax_id_number
        if tax_id_enum_type is not UNSET:
            field_dict["taxIdEnumType"] = tax_id_enum_type
        if date_of_birth is not UNSET:
            field_dict["dateOfBirth"] = date_of_birth
        if portfolio_number is not UNSET:
            field_dict["portfolioNumber"] = portfolio_number
        if port_sequence is not UNSET:
            field_dict["portSequence"] = port_sequence
        if tax_id_type is not UNSET:
            field_dict["taxIdType"] = tax_id_type
        if phones is not UNSET:
            field_dict["Phones"] = phones
        if emails is not UNSET:
            field_dict["Emails"] = emails
        if addresses is not UNSET:
            field_dict["Addresses"] = addresses
        if account_associations is not UNSET:
            field_dict["accountAssociations"] = account_associations

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.customer_address import CustomerAddress
        from ..models.customer_contact_data import CustomerContactData
        from ..models.customer_phone_data import CustomerPhoneData
        from ..models.enrollment_account_association import EnrollmentAccountAssociation

        d = dict(src_dict)

        def _parse_name_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        name_id = _parse_name_id(d.pop("nameId", UNSET))

        def _parse_customer_type(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        customer_type = _parse_customer_type(d.pop("customerType", UNSET))

        def _parse_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_short_last_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        short_last_name = _parse_short_last_name(d.pop("shortLastName", UNSET))

        def _parse_short_first_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        short_first_name = _parse_short_first_name(d.pop("shortFirstName", UNSET))

        def _parse_middle_initial(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        middle_initial = _parse_middle_initial(d.pop("middleInitial", UNSET))

        def _parse_tax_id_code(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        tax_id_code = _parse_tax_id_code(d.pop("taxIdCode", UNSET))

        def _parse_tax_id_number(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        tax_id_number = _parse_tax_id_number(d.pop("taxIdNumber", UNSET))

        def _parse_tax_id_enum_type(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        tax_id_enum_type = _parse_tax_id_enum_type(d.pop("taxIdEnumType", UNSET))

        def _parse_date_of_birth(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        date_of_birth = _parse_date_of_birth(d.pop("dateOfBirth", UNSET))

        def _parse_portfolio_number(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        portfolio_number = _parse_portfolio_number(d.pop("portfolioNumber", UNSET))

        def _parse_port_sequence(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        port_sequence = _parse_port_sequence(d.pop("portSequence", UNSET))

        def _parse_tax_id_type(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        tax_id_type = _parse_tax_id_type(d.pop("taxIdType", UNSET))

        def _parse_phones(data: object) -> Union[None, Unset, list["CustomerPhoneData"]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                phones_type_0 = []
                _phones_type_0 = data
                for phones_type_0_item_data in _phones_type_0:
                    phones_type_0_item = CustomerPhoneData.from_dict(phones_type_0_item_data)

                    phones_type_0.append(phones_type_0_item)

                return phones_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list["CustomerPhoneData"]], data)

        phones = _parse_phones(d.pop("Phones", UNSET))

        def _parse_emails(data: object) -> Union[None, Unset, list["CustomerContactData"]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                emails_type_0 = []
                _emails_type_0 = data
                for emails_type_0_item_data in _emails_type_0:
                    emails_type_0_item = CustomerContactData.from_dict(emails_type_0_item_data)

                    emails_type_0.append(emails_type_0_item)

                return emails_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list["CustomerContactData"]], data)

        emails = _parse_emails(d.pop("Emails", UNSET))

        def _parse_addresses(data: object) -> Union[None, Unset, list["CustomerAddress"]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                addresses_type_0 = []
                _addresses_type_0 = data
                for addresses_type_0_item_data in _addresses_type_0:
                    addresses_type_0_item = CustomerAddress.from_dict(addresses_type_0_item_data)

                    addresses_type_0.append(addresses_type_0_item)

                return addresses_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list["CustomerAddress"]], data)

        addresses = _parse_addresses(d.pop("Addresses", UNSET))

        def _parse_account_associations(data: object) -> Union[None, Unset, list["EnrollmentAccountAssociation"]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                account_associations_type_0 = []
                _account_associations_type_0 = data
                for account_associations_type_0_item_data in _account_associations_type_0:
                    account_associations_type_0_item = EnrollmentAccountAssociation.from_dict(
                        account_associations_type_0_item_data
                    )

                    account_associations_type_0.append(account_associations_type_0_item)

                return account_associations_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list["EnrollmentAccountAssociation"]], data)

        account_associations = _parse_account_associations(d.pop("accountAssociations", UNSET))

        soa_enrollment_customer_account = cls(
            name_id=name_id,
            customer_type=customer_type,
            name=name,
            short_last_name=short_last_name,
            short_first_name=short_first_name,
            middle_initial=middle_initial,
            tax_id_code=tax_id_code,
            tax_id_number=tax_id_number,
            tax_id_enum_type=tax_id_enum_type,
            date_of_birth=date_of_birth,
            portfolio_number=portfolio_number,
            port_sequence=port_sequence,
            tax_id_type=tax_id_type,
            phones=phones,
            emails=emails,
            addresses=addresses,
            account_associations=account_associations,
        )

        return soa_enrollment_customer_account

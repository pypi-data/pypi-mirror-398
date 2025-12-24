from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..models.account_type import AccountType
from ..types import UNSET, Unset

T = TypeVar("T", bound="EnrollmentAccountAssociation")


@_attrs_define
class EnrollmentAccountAssociation:
    """
    Attributes:
        account_number (Union[None, Unset, str]):
        account_type (Union[Unset, AccountType]):
        portfolio (Union[None, Unset, str]):
        tax_id_name (Union[None, Unset, str]):
        class_code (Union[Unset, int]):
        primary_owner_code (Union[Unset, int]):
        account_type_code (Union[Unset, int]):
        portfolio_number (Union[None, Unset, str]):
        responsibility_code (Union[None, Unset, str]):
        product_number (Union[Unset, int]):
        is_business_account (Union[Unset, bool]):
        port_sequence (Union[None, Unset, str]):
        can_withdraw (Union[Unset, bool]):
        can_deposit (Union[Unset, bool]):
        can_view (Union[Unset, bool]):
        related_to_id_type (Union[None, Unset, str]):
        name_id (Union[None, Unset, str]):
        relationship_code (Union[None, Unset, str]):
        direct_indirect_code (Union[None, Unset, str]):
    """

    account_number: Union[None, Unset, str] = UNSET
    account_type: Union[Unset, AccountType] = UNSET
    portfolio: Union[None, Unset, str] = UNSET
    tax_id_name: Union[None, Unset, str] = UNSET
    class_code: Union[Unset, int] = UNSET
    primary_owner_code: Union[Unset, int] = UNSET
    account_type_code: Union[Unset, int] = UNSET
    portfolio_number: Union[None, Unset, str] = UNSET
    responsibility_code: Union[None, Unset, str] = UNSET
    product_number: Union[Unset, int] = UNSET
    is_business_account: Union[Unset, bool] = UNSET
    port_sequence: Union[None, Unset, str] = UNSET
    can_withdraw: Union[Unset, bool] = UNSET
    can_deposit: Union[Unset, bool] = UNSET
    can_view: Union[Unset, bool] = UNSET
    related_to_id_type: Union[None, Unset, str] = UNSET
    name_id: Union[None, Unset, str] = UNSET
    relationship_code: Union[None, Unset, str] = UNSET
    direct_indirect_code: Union[None, Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        account_number: Union[None, Unset, str]
        if isinstance(self.account_number, Unset):
            account_number = UNSET
        else:
            account_number = self.account_number

        account_type: Union[Unset, str] = UNSET
        if not isinstance(self.account_type, Unset):
            account_type = self.account_type.value

        portfolio: Union[None, Unset, str]
        if isinstance(self.portfolio, Unset):
            portfolio = UNSET
        else:
            portfolio = self.portfolio

        tax_id_name: Union[None, Unset, str]
        if isinstance(self.tax_id_name, Unset):
            tax_id_name = UNSET
        else:
            tax_id_name = self.tax_id_name

        class_code = self.class_code

        primary_owner_code = self.primary_owner_code

        account_type_code = self.account_type_code

        portfolio_number: Union[None, Unset, str]
        if isinstance(self.portfolio_number, Unset):
            portfolio_number = UNSET
        else:
            portfolio_number = self.portfolio_number

        responsibility_code: Union[None, Unset, str]
        if isinstance(self.responsibility_code, Unset):
            responsibility_code = UNSET
        else:
            responsibility_code = self.responsibility_code

        product_number = self.product_number

        is_business_account = self.is_business_account

        port_sequence: Union[None, Unset, str]
        if isinstance(self.port_sequence, Unset):
            port_sequence = UNSET
        else:
            port_sequence = self.port_sequence

        can_withdraw = self.can_withdraw

        can_deposit = self.can_deposit

        can_view = self.can_view

        related_to_id_type: Union[None, Unset, str]
        if isinstance(self.related_to_id_type, Unset):
            related_to_id_type = UNSET
        else:
            related_to_id_type = self.related_to_id_type

        name_id: Union[None, Unset, str]
        if isinstance(self.name_id, Unset):
            name_id = UNSET
        else:
            name_id = self.name_id

        relationship_code: Union[None, Unset, str]
        if isinstance(self.relationship_code, Unset):
            relationship_code = UNSET
        else:
            relationship_code = self.relationship_code

        direct_indirect_code: Union[None, Unset, str]
        if isinstance(self.direct_indirect_code, Unset):
            direct_indirect_code = UNSET
        else:
            direct_indirect_code = self.direct_indirect_code

        field_dict: dict[str, Any] = {}
        field_dict.update({})
        if account_number is not UNSET:
            field_dict["accountNumber"] = account_number
        if account_type is not UNSET:
            field_dict["accountType"] = account_type
        if portfolio is not UNSET:
            field_dict["portfolio"] = portfolio
        if tax_id_name is not UNSET:
            field_dict["taxIdName"] = tax_id_name
        if class_code is not UNSET:
            field_dict["classCode"] = class_code
        if primary_owner_code is not UNSET:
            field_dict["primaryOwnerCode"] = primary_owner_code
        if account_type_code is not UNSET:
            field_dict["accountTypeCode"] = account_type_code
        if portfolio_number is not UNSET:
            field_dict["portfolioNumber"] = portfolio_number
        if responsibility_code is not UNSET:
            field_dict["responsibilityCode"] = responsibility_code
        if product_number is not UNSET:
            field_dict["productNumber"] = product_number
        if is_business_account is not UNSET:
            field_dict["isBusinessAccount"] = is_business_account
        if port_sequence is not UNSET:
            field_dict["portSequence"] = port_sequence
        if can_withdraw is not UNSET:
            field_dict["canWithdraw"] = can_withdraw
        if can_deposit is not UNSET:
            field_dict["canDeposit"] = can_deposit
        if can_view is not UNSET:
            field_dict["canView"] = can_view
        if related_to_id_type is not UNSET:
            field_dict["relatedToIdType"] = related_to_id_type
        if name_id is not UNSET:
            field_dict["nameId"] = name_id
        if relationship_code is not UNSET:
            field_dict["relationshipCode"] = relationship_code
        if direct_indirect_code is not UNSET:
            field_dict["directIndirectCode"] = direct_indirect_code

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_account_number(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        account_number = _parse_account_number(d.pop("accountNumber", UNSET))

        _account_type = d.pop("accountType", UNSET)
        account_type: Union[Unset, AccountType]
        if isinstance(_account_type, Unset):
            account_type = UNSET
        else:
            account_type = AccountType(_account_type)

        def _parse_portfolio(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        portfolio = _parse_portfolio(d.pop("portfolio", UNSET))

        def _parse_tax_id_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        tax_id_name = _parse_tax_id_name(d.pop("taxIdName", UNSET))

        class_code = d.pop("classCode", UNSET)

        primary_owner_code = d.pop("primaryOwnerCode", UNSET)

        account_type_code = d.pop("accountTypeCode", UNSET)

        def _parse_portfolio_number(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        portfolio_number = _parse_portfolio_number(d.pop("portfolioNumber", UNSET))

        def _parse_responsibility_code(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        responsibility_code = _parse_responsibility_code(d.pop("responsibilityCode", UNSET))

        product_number = d.pop("productNumber", UNSET)

        is_business_account = d.pop("isBusinessAccount", UNSET)

        def _parse_port_sequence(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        port_sequence = _parse_port_sequence(d.pop("portSequence", UNSET))

        can_withdraw = d.pop("canWithdraw", UNSET)

        can_deposit = d.pop("canDeposit", UNSET)

        can_view = d.pop("canView", UNSET)

        def _parse_related_to_id_type(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        related_to_id_type = _parse_related_to_id_type(d.pop("relatedToIdType", UNSET))

        def _parse_name_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        name_id = _parse_name_id(d.pop("nameId", UNSET))

        def _parse_relationship_code(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        relationship_code = _parse_relationship_code(d.pop("relationshipCode", UNSET))

        def _parse_direct_indirect_code(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        direct_indirect_code = _parse_direct_indirect_code(d.pop("directIndirectCode", UNSET))

        enrollment_account_association = cls(
            account_number=account_number,
            account_type=account_type,
            portfolio=portfolio,
            tax_id_name=tax_id_name,
            class_code=class_code,
            primary_owner_code=primary_owner_code,
            account_type_code=account_type_code,
            portfolio_number=portfolio_number,
            responsibility_code=responsibility_code,
            product_number=product_number,
            is_business_account=is_business_account,
            port_sequence=port_sequence,
            can_withdraw=can_withdraw,
            can_deposit=can_deposit,
            can_view=can_view,
            related_to_id_type=related_to_id_type,
            name_id=name_id,
            relationship_code=relationship_code,
            direct_indirect_code=direct_indirect_code,
        )

        return enrollment_account_association

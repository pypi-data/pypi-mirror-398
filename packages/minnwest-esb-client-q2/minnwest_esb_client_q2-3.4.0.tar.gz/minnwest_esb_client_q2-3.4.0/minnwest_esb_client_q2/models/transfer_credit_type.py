from enum import Enum


class TransferCreditType(str, Enum):
    CHECKING = "Checking"
    DEPOSIT = "Deposit"
    LOAN = "Loan"
    SAVINGS = "Savings"

    def __str__(self) -> str:
        return str(self.value)

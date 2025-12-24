from enum import Enum


class AccountType(str, Enum):
    CARD = "Card"
    CERTIFICATE = "Certificate"
    CHECKING = "Checking"
    DDALOAN = "DdaLoan"
    LOAN = "Loan"
    NONE = "None"
    SAFEDEPOSITBOX = "SafeDepositBox"
    SAVINGS = "Savings"
    UNKNOWN = "Unknown"

    def __str__(self) -> str:
        return str(self.value)

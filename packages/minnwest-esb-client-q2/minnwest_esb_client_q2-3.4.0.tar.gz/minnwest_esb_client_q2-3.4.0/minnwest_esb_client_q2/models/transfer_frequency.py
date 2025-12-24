from enum import Enum


class TransferFrequency(str, Enum):
    EVERYTWOMONTHS = "EveryTwoMonths"
    EVERYTWOWEEKS = "EveryTwoWeeks"
    MONTHLY = "Monthly"
    NONE = "None"
    ONCE = "Once"
    QUARTERLY = "Quarterly"
    SEMIANNUALLY = "Semiannually"
    TWICEMONTHLY = "TwiceMonthly"
    WEEKLY = "Weekly"
    YEARLY = "Yearly"

    def __str__(self) -> str:
        return str(self.value)

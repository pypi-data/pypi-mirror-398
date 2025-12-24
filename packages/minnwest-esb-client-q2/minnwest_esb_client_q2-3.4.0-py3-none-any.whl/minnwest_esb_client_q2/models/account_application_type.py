from enum import Enum


class AccountApplicationType(str, Enum):
    COD = "COD"
    CRD = "CRD"
    DDA = "DDA"
    LAS = "LAS"
    LINES = "Lines"
    NONE = "None"
    PORT = "PORT"
    SAV = "SAV"
    SDB = "SDB"

    def __str__(self) -> str:
        return str(self.value)

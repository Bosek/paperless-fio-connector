from datetime import datetime
from typing import NamedTuple

from price_parser.parser import Price


class Transaction(NamedTuple):
    ID: int
    Date: str
    Amount: int
    Currency: str
    Account: str
    IsIBAN: bool
    Message: str | None
    VS: str | None
    Specification: str | None

    def get_foreign_amount(self) -> Price | None:
        if self.Specification is not None:
            return Price.fromstring(self.Specification)
        else:
            return None
        
    def get_date(self) -> datetime:
        return datetime.fromisoformat(self.Date)
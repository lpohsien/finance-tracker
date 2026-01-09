from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Optional
from dateutil import parser as date_parser

@dataclass
class TransactionData:
    type: str
    amount: float
    description: str
    bank: str
    id: Optional[str] = None
    account: Optional[str] = None
    timestamp: Optional[str] = None
    category: Optional[str] = None
    raw_message: Optional[str] = None
    status: Optional[str] = None

    def __post_init__(self):
        # Validate timestamp
        if self.timestamp:
            try:
                date_parser.isoparse(self.timestamp)
            except Exception:
                 raise ValueError(f"Invalid timestamp format: {self.timestamp}")

        # Validate amount
        if not isinstance(self.amount, (int, float)):
             try:
                 self.amount = float(self.amount)
             except ValueError:
                 raise ValueError(f"Invalid amount: {self.amount}")

    def to_dict(self):
        return asdict(self)
    

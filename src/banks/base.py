from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Tuple

class BaseBankParser(ABC):

    transaction_types = [
        "Transfer",
        "Card",
        "PayNow",
        "NETS QR",
    ]

    @abstractmethod
    def rule_parse(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Parses the bank message text.
        Returns a dictionary with:
        - type: str (standardized transaction type)
        - amount: float (signed, negative for expense, positive for income)
        - description: str (merchant or recipient)
        - account: str (account number/identifier)
        - timestamp: datetime (optional, parsed from message)
        """
        pass

    def llm_parse(self, text: str) -> Tuple[Optional[Dict[str, str|float|None]], Optional[str]]:
        """
        Placeholder for LLM-based parsing method.
        This can be implemented in subclasses if needed.
        """
        from src.llm_helper import llm_parse_bank_message
        return llm_parse_bank_message(text, self.transaction_types)
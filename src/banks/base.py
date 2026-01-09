from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Tuple
from src.models import TransactionData

class BaseBankParser(ABC):

    transaction_types = [
        "Transfer",
        "Card",
        "PayNow",
        "NETS QR",
    ]

    @abstractmethod
    def rule_parse(self, text: str) -> Optional[TransactionData]:
        """
        Parses the bank message text.
        Returns a TransactionData object.
        """
        pass

    def llm_parse(self, text: str) -> Tuple[Optional[TransactionData], Optional[str]]:
        """
        Placeholder for LLM-based parsing method.
        This can be implemented in subclasses if needed.
        """
        from src.llm_helper import llm_parse_bank_message
        parsed_dict, error = llm_parse_bank_message(text, self.transaction_types)

        if error or not parsed_dict:
            return None, error

        # Convert dict to TransactionData
        try:
            # llm_parse_bank_message returns dict with keys: type, amount, description, account, timestamp
            # We need to ensure 'bank' is set (though it might be set by the caller,
            # the dataclass requires it. We can set a placeholder or require the caller to fill it)
            # The current BaseBankParser doesn't know the bank name unless passed.
            # However, llm_parse is called by TransactionParser which knows the bank.
            # But here we are returning TransactionData.
            # I'll set bank to "Unknown" or allowing None if I relax the model,
            # but the model has bank: str.
            # I will set it to "Generic" or "LLM" for now, and let TransactionParser override it.

            data = TransactionData(
                type=parsed_dict.get("type", "Unknown"),
                amount=parsed_dict.get("amount", 0.0),
                description=parsed_dict.get("description", "Unknown"),
                bank="LLM", # Temporary, should be updated by caller
                account=parsed_dict.get("account"),
                timestamp=parsed_dict.get("timestamp")
            )
            return data, None
        except Exception as e:
            return None, f"Failed to convert LLM output to TransactionData: {e}"

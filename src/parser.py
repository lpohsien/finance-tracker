import re
import logging
import uuid
from datetime import datetime
from dateutil import parser as date_parser
from typing import List, Optional, Tuple
from src.llm_helper import categorize_transaction
from src.banks import UOBParser
from src.models import TransactionData

logger = logging.getLogger(__name__)

class TransactionParser:
    def __init__(self):
        self.bank_parsers = {
            "UOB": UOBParser(),
        }

    def parse_message(self, full_message: str, categories_list: Optional[List] = None) -> Tuple[Optional[TransactionData], Optional[str]]:
        """
        Parses the composite message from Apple Shortcuts.
        Format: "{Bank_Msg},{bank},{ISO_Timestamp},{Remarks}"
        """
        # Split the message. We expect the ISO timestamp to be the anchor.
        # Regex to find the ISO timestamp in the middle
        # 2025-12-28T15:57:31+08:00
        status = None
        split_pattern = re.compile(r"(.*),(\w+),(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}),(.*)", re.DOTALL)
        match = split_pattern.match(full_message)
        
        if not match:
            logger.error(f"Failed to split message: {full_message}")
            return None, "Invalid message format"

        bank_msg = match.group(1).strip()
        bank_name = match.group(2).strip()
        shortcut_timestamp_str = match.group(3).strip()
        remarks = match.group(4).strip()

        # Select parser based on bank name
        parser = self.bank_parsers.get(bank_name)
        if not parser:
            logger.error(f"No parser found for bank: {bank_name}")
            return None, "Unsupported bank"

        # Try parsing the bank message using regex rules
        parsed_data = parser.rule_parse(bank_msg)
        if not parsed_data:
            logger.info(f"Message ignored or failed to parse bank text: {bank_msg}")
            status = f"Warning: No parsing rules matched for bank message: <blockquote expandable>{bank_msg}</blockquote>"

            # If no parsing rules matched, use LLM-based parsing
            parsed_data, llm_err = parser.llm_parse(bank_msg)
            if not parsed_data:
                return None, f"LLM-parsing failed for <blockquote expandable>{llm_err}</blockquote>. Full message: <pre>{bank_msg}</pre>"
            
            # Append to status that LLM was used
            status = "⚠️ Used LLM parsing. Verify details."
        
        if parsed_data.status and parser.TIME_PARSE_WARNING in parsed_data.status:
            # use shortcut_timestamp_str if the parser time and shortcut time is within the same day, else keep parser status
            try:
                parser_time = date_parser.isoparse(parsed_data.timestamp)
                shortcut_time = date_parser.isoparse(shortcut_timestamp_str)
                if parser_time.date() == shortcut_time.date():
                    parsed_data.timestamp = shortcut_timestamp_str
            except Exception as e:
                logger.error(f"Failed to compare timestamps: {e}")
                # keep existing status

        # Ensure bank field is correct (especially if LLM parsed it as generic)
        if parsed_data.bank == "LLM" or not parsed_data.bank:
             parsed_data.bank = bank_name
        elif parsed_data.bank != bank_name:
             logger.warning(f"Parsed bank {parsed_data.bank} differs from shortcut bank {bank_name}. Using parser's value if valid, or shortcut's.")
             return None, f"Bank name mismatch: parsed '{parsed_data.bank}' vs shortcut '{bank_name}'"

        try:
            date_parser.isoparse(parsed_data.timestamp)
        except Exception as e:
            logger.error(f"Failed to parse shortcut timestamp '{parsed_data.timestamp}': {e}")
            return None, "Invalid timestamp format"

        # Categorization
        category = self._categorize(parsed_data, remarks, full_message, categories_list)

        # Description
        description = f"{remarks}" if remarks else ""
        description += f" [{parsed_data.description}]"

        # Update TransactionData
        parsed_data.description = description
        parsed_data.category = category
        parsed_data.raw_message = full_message

        if parsed_data.status:
            if status:
                parsed_data.status += status # Assigning status to the object as requested
        else:
            parsed_data.status = status  

        return parsed_data, status

    def _categorize(self, parsed_data: TransactionData, remarks: str, full_message: str, categories_list: Optional[List[str]] = None) -> str:
        # 1. Keyword based (Simple)
        description = parsed_data.description or ""
        text_to_check = (description + " " + remarks).lower()

        if categories_list:
             keywords = { cat: [cat.lower()] for cat in categories_list }
        else:
             # Fallback if no categories list provided (should not happen with current bot logic)
             keywords = {}

        if "disbursement" in text_to_check:
            return "Disbursement"
        
        # Add default keywords if category exists in user list
        if "Food" in keywords: keywords["Food"].extend(["dinner", "lunch", "breakfast", "cafe", "restaurant", "mcdonald", "kfc", "food"])
        if "Snack" in keywords: keywords["Snack"].extend(["snacks", "coffee", "bubble tea", "tea", "drink", "drinks"])
        if "Transport" in keywords: keywords["Transport"].extend([ "grab", "gojek", "uber", "taxi", "train", "bus", "mrt", "concession", "smrt"])
        if "Shopping" in keywords: keywords["Shopping"].extend(["shopee", "lazada", "amazon", "uniqlo"])
        if "Groceries" in keywords: keywords["Groceries"].extend(["grocery", "fairprice", "cold storage", "giant", "market"])
        if "Utilities" in keywords: keywords["Utilities"].extend(["singtel", "starhub", "m1", "electricity", "water"])

        for cat, words in keywords.items():
            if any(word in text_to_check for word in words):
                return cat

        # 2. LLM Fallback
        return categorize_transaction(full_message, categories_list)

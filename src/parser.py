import re
import logging
import uuid
from datetime import datetime
from dateutil import parser as date_parser
from dateutil import tz
from typing import Optional, Dict, Any
from src.llm_helper import categorize_transaction

logger = logging.getLogger(__name__)

class TransactionParser:
    def __init__(self):
        # Regex patterns for different transaction types
        self.patterns = [
            {
                "type": "PayNow Outgoing",
                "regex": re.compile(r"You made a PayNow transfer of SGD (?P<amount>[\d\.]+) to (?P<recipient>.+?) on your a/c ending (?P<account>\d+) at (?P<datetime_str>.+?)\. If unauthorised"),
                "sign": -1
            },
            {
                "type": "PayNow Incoming",
                "regex": re.compile(r"You have received SGD (?P<amount>[\d\.]+) in your PayNow-linked account ending (?P<account>\d+) on (?P<datetime_str>.+?)\."),
                "sign": 1
            },
            {
                "type": "Card Transaction",
                "regex": re.compile(r"A transaction of SGD (?P<amount>[\d\.]+) was made with your UOB Card ending (?P<account>\d+) on (?P<date_str>.+?) at (?P<merchant>.+?)\. If unauthorised"),
                "sign": -1
            }
        ]

    def parse_message(self, full_message: str) -> Optional[Dict[str, Any]]:
        """
        Parses the composite message from Apple Shortcuts.
        Format: "{Bank_Msg},{ISO_Timestamp},{Remarks}"
        """
        # Split the message. We expect the ISO timestamp to be the anchor.
        # Regex to find the ISO timestamp in the middle
        # 2025-12-28T15:57:31+08:00
        split_pattern = re.compile(r"(.*),(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}),(.*)", re.DOTALL)
        match = split_pattern.match(full_message)
        
        if not match:
            logger.error(f"Failed to split message: {full_message}")
            return None

        bank_msg = match.group(1).strip()
        shortcut_timestamp_str = match.group(2).strip()
        remarks = match.group(3).strip()

        parsed_data = self._parse_bank_message(bank_msg)
        
        if not parsed_data:
            logger.info(f"Message ignored or failed to parse bank text: {bank_msg}")
            return None

        # Determine final timestamp
        final_timestamp = None
        if parsed_data.get("datetime_str"):
            try:
                # Clean up UOB date formats if needed
                dt_str = parsed_data["datetime_str"].replace(" at ", " ")
                # Handle "1:44PM SGT, 27 Dec 25" -> remove SGT for dateutil if it confuses it, 
                # but dateutil is usually good.
                # UOB: "1:44PM SGT, 27 Dec 25"
                tzinfos = {"SGT": tz.gettz("Asia/Singapore")}
                final_timestamp = date_parser.parse(dt_str, fuzzy=True, tzinfos=tzinfos)
            except Exception as e:
                logger.warning(f"Failed to parse bank timestamp '{parsed_data['datetime_str']}': {e}")
        
        if not final_timestamp and parsed_data.get("date_str"):
             # Card transaction only has date, use shortcut timestamp for time if possible, 
             # but spec says "use the ISO timestamp at the end for storage" for Type 3.
             pass

        if not final_timestamp:
            try:
                final_timestamp = date_parser.isoparse(shortcut_timestamp_str)
            except Exception as e:
                logger.error(f"Failed to parse shortcut timestamp '{shortcut_timestamp_str}': {e}")
                return None

        # Categorization
        category = self._categorize(parsed_data, remarks, full_message)

        # Description
        description = f"{remarks}" if remarks else ""
        description += f" [{parsed_data.get("merchant") or parsed_data.get("recipient") or "Unknown"}]"

        # Generate UUID
        # We use the final timestamp and the raw message to ensure uniqueness and determinism
        transaction_id = str(uuid.uuid5(uuid.NAMESPACE_OID, f"{datetime.now()}|{full_message}"))

        # Construct result
        return {
            "id": transaction_id,
            "timestamp": final_timestamp.isoformat(),
            "type": parsed_data["type"],
            "amount": parsed_data["amount"] * parsed_data["sign"],
            "description": description,
            "account": parsed_data.get("account"),
            "category": category,
            "remarks": remarks,
            "raw_message": full_message
        }

    def _parse_bank_message(self, text: str) -> Optional[Dict[str, Any]]:
        for pattern in self.patterns:
            match = pattern["regex"].search(text)
            if match:
                data = match.groupdict()
                data["type"] = pattern["type"]
                data["sign"] = pattern["sign"]
                data["amount"] = float(data["amount"])
                return data
        return None

    def _categorize(self, parsed_data: Dict[str, Any], remarks: str, full_message: str) -> str:
        # 1. Keyword based (Simple)
        description = parsed_data.get("merchant") or parsed_data.get("recipient") or ""
        text_to_check = (description + " " + remarks).lower()
        
        keywords = {
            "Food": ["dinner", "lunch", "breakfast", "cafe", "restaurant", "mcdonald", "kfc", "food"],
            "Snacks": ["starbucks", "coffee", "bubble tea", "tea", "snack", "coffee", "tea"],
            "Transport": ["grab", "gojek", "uber", "taxi", "train", "bus", "mrt", "transport"],
            "Shopping": ["shopee", "lazada", "amazon", "supermarket", "mart", "uniqlo"],
            "Utilities": ["singtel", "starhub", "m1", "electricity", "water", "bill"],
        }

        for cat, words in keywords.items():
            if any(word in text_to_check for word in words):
                return cat

        # 2. LLM Fallback
        return categorize_transaction(full_message)

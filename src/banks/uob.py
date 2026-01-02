import re
from typing import Optional, Dict, Any
from dateutil import parser as date_parser
from dateutil import tz
from .base import BaseBankParser

class UOBParser(BaseBankParser):
    def __init__(self):
        self.patterns = [
            {
                "regex": re.compile(r"You made a (?P<method>.+?) of SGD (?P<amount>[\d\.,]+) to (?P<recipient>.+?) on your a/c ending (?P<account>\d+) at (?P<datetime_str>.+?)\. If unauthorised"),
                "sign": -1
            },
            {
                "regex": re.compile(r"You made a (?P<method>.+?) of SGD (?P<amount>[\d\.,]+) to (?P<recipient>.+?) at (?P<datetime_str>.+?), on your a/c ending (?P<account>\d+)\. If unauthorised"),
                "sign": -1
            },
            {
                "regex": re.compile(r"You have received SGD (?P<amount>[\d\.,]+) in your (?P<method>PayNow)-linked account ending (?P<account>\d+) on (?P<datetime_str>.+?)\."),
                "sign": 1
            },
            {
                "regex": re.compile(r"A transaction of SGD (?P<amount>[\d\.,]+) was made with your UOB (?P<method>Card) ending (?P<account>\d+) on (?P<date_str>.+?) at (?P<recipient>.+?)\. If unauthorised"),
                "sign": -1
            }
        ]
        
        self.type_mapping = {
            "NETS QR payment": "NETS QR",
            "one-time transfer": "Transfer",
            "fund transfer": "Transfer",
            "fund transfer(s)": "Transfer",
            "PayNow transfer": "PayNow",
            "PayNow": "PayNow",
            "Card": "Card"
        }

        # Validate that all mapped types are known transaction types
        for type in self.type_mapping.values():
            if type not in self.transaction_types:
                raise ValueError(f"Unknown transaction type mapping: {type}")

    def rule_parse(self, text: str) -> Optional[Dict[str, Any]]:
        for pattern in self.patterns:
            match = pattern["regex"].search(text)
            if match:
                data = match.groupdict()
                
                # Determine raw type
                raw_type: str = data.get("method")
                
                # Map to standardized type
                # If exact match not found, try partial match or default to raw_type
                std_type = self.type_mapping.get(raw_type, raw_type)
                
                # If raw_type is not in mapping, try to see if any key is part of raw_type
                if raw_type not in self.type_mapping:
                    for key, val in self.type_mapping.items():
                        if key in raw_type:
                            std_type = val
                            break

                # Amount
                sign = int(pattern["sign"])
                amount = float(data["amount"].replace(',', '')) * sign
                
                # Description
                description = data.get("recipient") or "Unknown"
                
                # Timestamp parsing
                timestamp = None
                if data.get("datetime_str"):
                    try:
                        dt_str = data["datetime_str"].replace(" at ", " ")
                        tzinfos = {"SGT": tz.gettz("Asia/Singapore")}
                        timestamp = date_parser.parse(dt_str, fuzzy=True, tzinfos=tzinfos).isoformat()
                    except Exception:
                        pass
                
                return {
                    "type": std_type,
                    "amount": amount,
                    "description": description,
                    "account": str(data.get("account")),
                    "timestamp": timestamp
                }
        return None

import pytest
from src.parser import TransactionParser

@pytest.fixture
def parser():
    return TransactionParser()

def test_parse_paynow_outgoing(parser):
    msg = "You made a PayNow transfer of SGD 19.36 to PAYNOW - SUPPORTED B (UEN ending C002) on your a/c ending 1234 at 1:44PM SGT, 27 Dec 25. If unauthorised, call UOB 24/7 Fraud Hotline.,UOB,2025-12-28T15:57:31+08:00, Lunch with friends"
    result, _ = parser.parse_message(msg)
    
    assert result is not None
    assert result["type"] == "PayNow"  # Updated to match UOBParser output
    assert result["amount"] == -19.36
    assert result["account"] == "1234"
    assert "PAYNOW - SUPPORTED B (UEN ending C002)" in result["description"]
    # remarks is merged into description in TransactionParser, not returned as a separate key
    assert "Lunch with friends" in result["description"]
    # Check date parsing logic - should prioritize bank msg
    # 27 Dec 25 1:44PM -> 2025-12-27 13:44:00
    assert "2025-12-27T13:44:00" in result["timestamp"]
def test_parse_paynow_incoming(parser):
    msg = "You have received SGD 18.62 in your PayNow-linked account ending 5678 on 07-MAY-2025 01:42AM.,UOB,2025-12-28T15:57:31+08:00, Refund"
    result, status = parser.parse_message(msg)
    
    assert result is not None
    assert status is None
    assert result["type"] == "PayNow" # Updated to match UOBParser output
    assert result["amount"] == 18.62
    assert result["account"] == "5678"
    assert "Refund" in result["description"]
    # 07-MAY-2025 01:42AM -> 2025-05-07 01:42:00
    assert "2025-05-07T01:42:00" in result["timestamp"]
    

def test_parse_card_transaction(parser):
    msg = "A transaction of SGD 15.00 was made with your UOB Card ending 9012 on 26/12/25 at JINJJA CHICKEN @ JEWEL. If unauthorised, call 24/7 Fraud Hotline now,UOB,2025-12-28T15:57:31+08:00, Dinner"
    result, status = parser.parse_message(msg)
    
    assert result is not None
    assert status is None
    assert result["type"] == "Card" # Updated to match UOBParser output
    assert result["amount"] == -15.00
    assert result["account"] == "9012"
    assert "JINJJA CHICKEN" in result["description"]
    assert "Dinner" in result["description"]
    # Card transaction only has date in bank msg, so we will use the shortcut timestamp instead.
    assert "2025-12-28" in result["timestamp"]


def test_ignore_message(parser):
    bank_msg = "We’ve enhanced your UOB One Debit Card! ..."
    bank_parser = parser.bank_parsers.get("UOB")
    assert bank_parser is not None
    
    # Make sure the rule based parser ignores this message
    rule_result = bank_parser.rule_parse(bank_msg)
    assert rule_result is None



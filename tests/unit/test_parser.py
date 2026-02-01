import pytest
from src.parser import TransactionParser
from src.models import TransactionData

@pytest.fixture
def parser():
    return TransactionParser()

def test_parse_paynow_outgoing(parser):
    msg = "You made a PayNow transfer of SGD 19.36 to PAYNOW - SUPPORTED B (UEN ending C002) on your a/c ending 1234 at 1:44PM SGT, 27 Dec 25. If unauthorised, call UOB 24/7 Fraud Hotline.,UOB,2025-12-28T15:57:31+08:00, Lunch with friends"
    result, _ = parser.parse_message(msg)

    assert result is not None
    assert isinstance(result, TransactionData)
    assert result.type == "PayNow"  # Updated to match UOBParser output
    assert result.amount == -19.36
    assert "Lunch with friends" in result.description
    assert result.account == "1234"
    assert result.bank == "UOB"

def test_parse_paynow_incoming(parser):
    msg = "You have received SGD 18.62 in your PayNow-linked account ending 5678 on 07-MAY-2025 01:42AM.,UOB,2025-12-28T15:57:31+08:00, Refund"
    result, status = parser.parse_message(msg)

    assert result is not None
    assert status is None
    assert isinstance(result, TransactionData)
    assert result.type == "PayNow" # Updated to match UOBParser output
    assert result.amount == 18.62
    assert "Refund" in result.description
    assert result.account == "5678"
    assert result.bank == "UOB"


def test_parse_card_transaction(parser):
    msg = "A transaction of SGD 15.00 was made with your UOB Card ending 9012 on 26/12/25 at JINJJA CHICKEN @ JEWEL. If unauthorised, call 24/7 Fraud Hotline now,UOB,2025-12-28T15:57:31+08:00, Dinner"
    result, status = parser.parse_message(msg)

    assert result is not None
    assert status is None
    assert isinstance(result, TransactionData)
    assert result.type == "Card" # Updated to match UOBParser output
    assert result.amount == -15.00
    assert "JINJJA CHICKEN @ JEWEL" in result.description
    assert "Dinner" in result.description
    assert result.account == "9012"
    assert result.bank == "UOB"

def test_invalid_bank_msg_but_valid_format(parser):
    # This should fail to parse bank msg, but because we mock LLM or if LLM fails, it might return None or status
    # In this environment LLM is disabled/no key, so it returns LLM parsing failed.
    msg = "Invalid Bank Message,UOB,2025-12-28T15:57:31+08:00, Something"
    result, status = parser.parse_message(msg)
    
    # Expect None because LLM fails and regex fails
    assert result is None
    assert "LLM-parsing failed" in status

def test_timestamp_use_message_time(parser):
    msg = "You made a PayNow transfer of SGD 20.00 to xyz (Mobile ending 1234) on your a/c ending 4567 at 12:38PM SGT, 9 Jan 26. If unauthorised, call UOB 24/7 Fraud Hotline.,UOB,2026-01-09T12:38:57+08:00, lunch - farewell lunch -  sanook kitchen - jewel"
    result, status = parser.parse_message(msg)

    assert result is not None
    assert result.status is None
    assert result.timestamp is not None and result.timestamp == "2026-01-09T12:38:00+08:00"

def test_timestamp_same_day_modify_time(parser):
    msg = "A transaction of SGD 100.00 was made with your UOB Card ending 3456 on 09/01/2026 at Gift Shop. If unauthorised, call 24/7 Fraud Hotline now,UOB,2026-01-09T22:08:02+08:00, Birthday Gift"
    result, status = parser.parse_message(msg)

    assert result is not None
    assert result.status is not None
    assert "TIME_PARSE_WARNING" in result.status
    assert result.timestamp is not None and result.timestamp == "2026-01-09T22:08:02+08:00"

def test_timestamp_diff_day_no_modify_time(parser):
    msg = "A transaction of SGD 100.00 was made with your UOB Card ending 3456 on 26/12/2025 at Gift Shop. If unauthorised, call 24/7 Fraud Hotline now,UOB,2025-12-25T15:57:31+08:00, Birthday Gift"
    result, status = parser.parse_message(msg)

    assert result is not None
    assert result.status is not None
    assert "TIME_PARSE_WARNING" in result.status
    assert result.timestamp is not None and result.timestamp == "2025-12-26T00:00:00+08:00"

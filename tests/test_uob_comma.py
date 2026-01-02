import pytest
from src.parser import TransactionParser

@pytest.fixture
def parser():
    return TransactionParser()

def test_parse_paynow_outgoing_with_comma(parser):
    msg = "You made a PayNow transfer of SGD 1,234.56 to PAYNOW - SUPPORTED B (UEN ending C002) on your a/c ending 1234 at 1:44PM SGT, 27 Dec 25. If unauthorised, call UOB 24/7 Fraud Hotline.,UOB,2025-12-28T15:57:31+08:00, Big Payment"
    result, err = parser.parse_message(msg)
    
    assert err is None
    assert result is not None
    assert result["type"] == "PayNow"
    assert result["amount"] == -1234.56
    assert result["account"] == "1234"

def test_parse_paynow_incoming_with_comma(parser):
    msg = "You have received SGD 10,000.00 in your PayNow-linked account ending 5678 on 07-MAY-2025 01:42AM.,UOB,2025-12-28T15:57:31+08:00, Bonus"
    result, err = parser.parse_message(msg)
    
    assert err is None
    assert result is not None
    assert result["type"] == "PayNow"
    assert result["amount"] == 10000.00
    assert result["account"] == "5678"

def test_parse_card_transaction_with_comma(parser):
    msg = "A transaction of SGD 2,500.50 was made with your UOB Card ending 9012 on 26/12/25 at LUXURY STORE. If unauthorised, call 24/7 Fraud Hotline now,UOB,2025-12-28T15:57:31+08:00, Shopping"
    result, err = parser.parse_message(msg)
    
    assert err is None
    assert result is not None
    assert result["type"] == "Card"
    assert result["amount"] == -2500.50
    assert result["account"] == "9012"

def test_parse_instalment_plan(parser):
    msg = "UOB Instalment Payment Plan: Your monthly instalment of SGD 1,200.00 has been billed to your UOB card ending 1234 on 01/01/26,UOB,2026-01-01T10:00:00+08:00, iPhone Installment"
    result, err = parser.parse_message(msg)
    
    assert err is None
    assert result is not None
    assert result["type"] == "Card"
    assert result["amount"] == -1200.00
    assert result["account"] == "1234"

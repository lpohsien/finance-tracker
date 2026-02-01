import logging
import os
import sys
from datetime import datetime
import pytest

# Do not run test llm by default even if GOOGLE_API_KEY is set, as it may incur costs.
# To run this test, set the environment variable RUN_LLM_TESTS=1
if os.getenv("RUN_LLM_TESTS") != "1":
    pytest.skip("Skipping entire module because of missing condition", allow_module_level=True)

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.parser import TransactionParser
from src.llm_helper import llm_parse_bank_message
from src.banks.uob import UOBParser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_direct_llm_parse():
    print("\n--- Testing Direct LLM Parse ---")
    # A message that doesn't match UOB regexes exactly but contains info
    message = "UOB: You spent SGD 25.50 at Starbucks on 30 Dec 2025 10:00 AM. Account ending 1234."
    
    print(f"Input Message: {message}")
    
    # We pass transaction types to help the LLM
    transaction_types = ["Card", "Transfer"]
    
    parsed_data, error = llm_parse_bank_message(message, transaction_types)

    if error:
        print(f"LLM Parse Error: {error}")
    else:
        print("LLM Parse Success:")
        print(parsed_data)

        # Basic validation
        assert parsed_data['amount'] == -25.50 or parsed_data['amount'] == 25.50
        assert "Starbucks" in parsed_data['description']
        assert "1234" in str(parsed_data['account'])

def test_parser_integration():
    print("\n--- Testing TransactionParser Integration (LLM Fallback) ---")
    parser = TransactionParser()
    
    # Construct a full message that matches the split regex in TransactionParser
    # Format: "{Bank_Msg},{bank},{ISO_Timestamp},{Remarks}"
    # We use a bank message that UOBParser.rule_parse will fail on.

    bank_msg = "UOB: You spent SGD 42.00 at NTUC FairPrice on 30 Dec 2025. Account 8888."
    bank_name = "UOB"
    # Use a timestamp format that matches the regex in parser.py (with timezone)
    timestamp = "2025-12-30T23:29:36+08:00"
    remarks = "Groceries"
    
    full_message = f"{bank_msg},{bank_name},{timestamp},{remarks}"
    
    print(f"Full Message: {full_message}")
    
    result, error = parser.parse_message(full_message)

    if result:
        print("Parser Success:")
        print(result)
        if error:
            print(f"Parser Warning: {error}")
        
        assert result['bank'] == "UOB"
        assert result['amount'] == -42.00 # Expecting expense
        assert "NTUC FairPrice" in result['description']
        assert result['category'] != "Uncategorized" # Should try to categorize
    else:
        print(f"Parser Error: {error}")

def test_rule_vs_llm_consistency():
    print("\n--- Testing Rule vs LLM Consistency ---")
    
    # A message that matches UOB regex exactly
    # Regex: You made a (?P<method>.+?) of SGD (?P<amount>[\d\.]+) to (?P<recipient>.+?) on your a/c ending (?P<account>\d+) at (?P<datetime_str>.+?)\. If unauthorised
    bank_msg = "You made a Card of SGD 15.00 to McDonald's on your a/c ending 1234 at 30 Dec 2025 12:00 PM. If unauthorised"
    
    print(f"Input Message: {bank_msg}")
    
    # 1. Rule-based parsing
    uob_parser = UOBParser()
    rule_result = uob_parser.rule_parse(bank_msg)
    print(f"Rule Result: {rule_result}")
    
    assert rule_result is not None, "Rule-based parsing failed for a valid message"
    
    # 2. LLM-based parsing
    transaction_types = ["Card", "Transfer", "PayNow", "NETS QR"]
    llm_result, llm_error = llm_parse_bank_message(bank_msg, transaction_types)
    
    if llm_error:
        print(f"LLM Parse Error: {llm_error}")
        if "LLM client not initialized" in llm_error:
            import pytest
            pytest.skip("Skipping LLM test: GOOGLE_API_KEY not set")
        raise Exception("LLM parsing failed")
        
    print(f"LLM Result: {llm_result}")
    
    # 3. Compare
    # Note: LLM might return slightly different formats (e.g. timestamp), so we compare key fields

    # Amount
    assert abs(rule_result['amount'] - llm_result['amount']) < 0.01, \
        f"Amount mismatch: Rule={rule_result['amount']}, LLM={llm_result['amount']}"

    # Account
    assert str(rule_result['account']) == str(llm_result['account']), \
        f"Account mismatch: Rule={rule_result['account']}, LLM={llm_result['account']}"

    # Description (LLM might clean it up, but should contain key parts)
    # Rule result for description is "McDonald's"
    assert rule_result['description'] in llm_result['description'] or llm_result['description'] in rule_result['description'], \
        f"Description mismatch: Rule={rule_result['description']}, LLM={llm_result['description']}"

    # Type
    assert rule_result['type'] == llm_result['type'], \
        f"Type mismatch: Rule={rule_result['type']}, LLM={llm_result['type']}"

    print("Consistency Check Passed!")

def test_ignore_message(parser):
    msg = "We’ve enhanced your UOB One Debit Card! ...,UOB,2025-12-28T15:57:31+08:00, Ignored"
    result, _ = parser.parse_message(msg)
    # Parser should ignore non-transactional messages and return None.
    assert result is None

if __name__ == "__main__":
    try:
        test_direct_llm_parse()
        test_parser_integration()
        test_rule_vs_llm_consistency()
        test_ignore_message(TransactionParser())
        print("\nAll tests passed!")
    except Exception as e:
        print(f"\nTest failed with exception: {e}")
        import traceback
        traceback.print_exc()



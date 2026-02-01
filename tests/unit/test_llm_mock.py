"""
Unit tests for the LLM mock functionality.

Tests:
- LLMMockResponse modes (valid, wrong_value, invalid, malformed)
- LLMCallTracker call limiting
- Response type detection (categorization vs parsing)
"""

import pytest
import json
from tests.conftest import LLMMockResponse, LLMCallTracker


class TestLLMMockResponse:
    """Tests for LLMMockResponse class."""
    
    def test_valid_mode_categorization(self):
        """Test valid mode returns expected category."""
        mock = LLMMockResponse(mode="valid")
        response = mock.get_categorization_response()
        assert response == "Food"
    
    def test_valid_mode_parsing(self):
        """Test valid mode returns properly structured parse response."""
        mock = LLMMockResponse(mode="valid")
        response = mock.get_parse_response()
        parsed = json.loads(response)
        
        assert "type" in parsed
        assert "amount" in parsed
        assert "description" in parsed
        assert "account" in parsed
        assert parsed["type"] == "Card"
        assert parsed["amount"] == -25.5
    
    def test_wrong_value_mode_categorization(self):
        """Test wrong_value mode returns invalid category."""
        mock = LLMMockResponse(mode="wrong_value")
        response = mock.get_categorization_response()
        assert response == "InvalidCategory"
    
    def test_wrong_value_mode_parsing(self):
        """Test wrong_value mode returns structure with wrong values."""
        mock = LLMMockResponse(mode="wrong_value")
        response = mock.get_parse_response()
        parsed = json.loads(response)
        
        assert parsed["type"] == "Unknown"
        assert parsed["amount"] == 0.0
        assert parsed["description"] == "Wrong"
    
    def test_invalid_mode_parsing(self):
        """Test invalid mode returns error response."""
        mock = LLMMockResponse(mode="invalid")
        response = mock.get_parse_response()
        assert response.startswith("ERROR:")
    
    def test_malformed_mode_categorization(self):
        """Test malformed mode returns non-parseable response."""
        mock = LLMMockResponse(mode="malformed")
        response = mock.get_categorization_response()
        assert "```" in response  # JSON in code block
    
    def test_malformed_mode_parsing(self):
        """Test malformed mode returns invalid JSON."""
        mock = LLMMockResponse(mode="malformed")
        response = mock.get_parse_response()
        
        # Should not be valid JSON
        with pytest.raises(json.JSONDecodeError):
            json.loads(response)
    
    def test_custom_category_override(self):
        """Test custom category overrides mode."""
        mock = LLMMockResponse(mode="valid", custom_category="Transport")
        response = mock.get_categorization_response()
        assert response == "Transport"
    
    def test_custom_parse_result_override(self):
        """Test custom parse result overrides mode."""
        custom_result = {
            "type": "PayNow",
            "amount": -100.00,
            "description": "Custom Merchant",
            "account": "9999",
            "timestamp": "2025-01-01T10:00:00"
        }
        mock = LLMMockResponse(mode="valid", custom_parse_result=custom_result)
        response = mock.get_parse_response()
        parsed = json.loads(response)
        
        assert parsed["type"] == "PayNow"
        assert parsed["amount"] == -100.00
        assert parsed["description"] == "Custom Merchant"
    
    def test_detect_categorization_call(self):
        """Test call type detection for categorization prompts."""
        mock = LLMMockResponse()
        
        categorization_prompts = [
            "Categorize this transaction into one of these categories: Food, Transport",
            "Return ONLY the category name",
            "You are a financial assistant. Categorize the following",
        ]
        
        for prompt in categorization_prompts:
            assert mock.detect_call_type(prompt) == "categorization"
    
    def test_detect_parsing_call(self):
        """Test call type detection for parsing prompts."""
        mock = LLMMockResponse()
        
        parsing_prompts = [
            "Parse the following bank message and extract the details",
            "Extract the following details from this transaction",
        ]
        
        for prompt in parsing_prompts:
            assert mock.detect_call_type(prompt) == "parsing"
    
    def test_response_for_prompt_categorization(self):
        """Test get_response_for_prompt returns category response."""
        mock = LLMMockResponse(mode="valid")
        prompt = "Categorize this transaction into Food or Transport"
        response = mock.get_response_for_prompt(prompt)
        assert response == "Food"
    
    def test_response_for_prompt_parsing(self):
        """Test get_response_for_prompt returns parse response."""
        mock = LLMMockResponse(mode="valid")
        prompt = "Parse the following bank message and extract transaction details"
        response = mock.get_response_for_prompt(prompt)
        parsed = json.loads(response)
        assert "type" in parsed
        assert "amount" in parsed


class TestLLMCallTracker:
    """Tests for LLMCallTracker class."""
    
    def test_initial_state(self):
        """Test tracker initializes with correct state."""
        tracker = LLMCallTracker(max_real_calls=3, skip_llm=False)
        
        assert tracker.call_count == 0
        assert tracker.max_real_calls == 3
        assert tracker.skip_llm is False
    
    def test_should_use_real_api_under_limit(self):
        """Test real API is used when under the call limit."""
        tracker = LLMCallTracker(max_real_calls=3, skip_llm=False)
        
        assert tracker.should_use_real_api() is True
        tracker.increment_call()
        assert tracker.should_use_real_api() is True
        tracker.increment_call()
        assert tracker.should_use_real_api() is True
    
    def test_should_not_use_real_api_at_limit(self):
        """Test mock is used when at the call limit."""
        tracker = LLMCallTracker(max_real_calls=3, skip_llm=False)
        
        for _ in range(3):
            tracker.increment_call()
        
        assert tracker.call_count == 3
        assert tracker.should_use_real_api() is False
    
    def test_should_not_use_real_api_when_skip_llm(self):
        """Test mock is always used when skip_llm is True."""
        tracker = LLMCallTracker(max_real_calls=3, skip_llm=True)
        
        assert tracker.should_use_real_api() is False
        assert tracker.call_count == 0
    
    def test_set_mock_mode(self):
        """Test setting mock mode changes responses."""
        tracker = LLMCallTracker(max_real_calls=0, skip_llm=True)
        
        # Default is valid
        response = tracker.get_mock_response("")
        assert response.text == "Food"
        
        # Change to wrong_value
        tracker.set_mock_mode("wrong_value")
        response = tracker.get_mock_response("")
        assert response.text == "InvalidCategory"
    
    def test_set_mock_mode_with_custom_category(self):
        """Test setting custom category in mock mode."""
        tracker = LLMCallTracker(max_real_calls=0, skip_llm=True)
        tracker.set_mock_mode("valid", custom_category="Shopping")
        
        response = tracker.get_mock_response("")
        assert response.text == "Shopping"
    
    def test_set_mock_mode_with_custom_parse_result(self):
        """Test setting custom parse result in mock mode."""
        tracker = LLMCallTracker(max_real_calls=0, skip_llm=True)
        
        custom_result = {"type": "NETS QR", "amount": -5.00, "description": "Hawker"}
        tracker.set_mock_mode("valid", custom_parse_result=custom_result)
        
        # Use a parsing prompt
        response = tracker.get_mock_response("Parse the bank message")
        parsed = json.loads(response.text)
        
        assert parsed["type"] == "NETS QR"
        assert parsed["amount"] == -5.00
    
    def test_get_mock_response_returns_mock_object(self):
        """Test get_mock_response returns a MagicMock-like object."""
        tracker = LLMCallTracker(max_real_calls=0, skip_llm=True)
        response = tracker.get_mock_response("")
        
        assert hasattr(response, "text")
        assert isinstance(response.text, str)


class TestLLMMockIntegration:
    """Integration tests for LLM mocking with real code patterns."""
    
    def test_mock_for_categorization_flow(self):
        """Test mock in a typical categorization flow."""
        tracker = LLMCallTracker(max_real_calls=0, skip_llm=True)
        
        # Simulate what categorize_transaction does
        categories_list = ["Food", "Transport", "Shopping"]
        prompt = f"Categorize the following transaction into one of these categories: {', '.join(categories_list)}"
        
        response = tracker.get_mock_response(prompt)
        category = response.text.strip()
        
        # Check if category is valid
        assert category in categories_list or category in ["InvalidCategory", "Other"]
    
    def test_mock_for_parsing_flow(self):
        """Test mock in a typical parsing flow."""
        tracker = LLMCallTracker(max_real_calls=0, skip_llm=True)
        
        # Simulate what llm_parse_bank_message does
        bank_message = "UOB: You spent SGD 25.50 at Starbucks"
        prompt = f"Parse the following bank message and extract transaction details: {bank_message}"
        
        response = tracker.get_mock_response(prompt)
        
        try:
            parsed_dict = json.loads(response.text)
            assert "type" in parsed_dict
            assert "amount" in parsed_dict
        except json.JSONDecodeError:
            # This is expected for error responses
            assert response.text.startswith("ERROR:")
    
    def test_negative_scenario_malformed_response(self):
        """Test how code should handle malformed LLM responses."""
        tracker = LLMCallTracker(max_real_calls=0, skip_llm=True)
        tracker.set_mock_mode("malformed")
        
        prompt = "Parse the following bank message"
        response = tracker.get_mock_response(prompt)
        
        # Code should handle this gracefully
        try:
            parsed = json.loads(response.text)
            # If it parses, check structure
            assert isinstance(parsed, dict)
        except json.JSONDecodeError:
            # This is the expected path for malformed responses
            pass
    
    def test_negative_scenario_error_response(self):
        """Test how code should handle error responses."""
        tracker = LLMCallTracker(max_real_calls=0, skip_llm=True)
        tracker.set_mock_mode("invalid")
        
        prompt = "Parse the following bank message"
        response = tracker.get_mock_response(prompt)
        
        # Code should detect ERROR prefix
        assert response.text.startswith("ERROR:") or response.text == ""

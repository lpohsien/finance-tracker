from typing import Dict, List, Optional, Tuple
from google import genai
from src.config import GOOGLE_API_KEY, DEFAULT_CATEGORIES, LLM_MODEL
import logging

logger = logging.getLogger(__name__)

def _init_llm_client(model: str = LLM_MODEL):
    if GOOGLE_API_KEY:
        client = genai.Client(api_key=GOOGLE_API_KEY)
    else:
        logger.warning("GOOGLE_API_KEY not set. LLM categorization will be disabled.")
        client = None
    return client

def categorize_transaction(message: str, categories_list: Optional[List] = None) -> str:
    """
    Uses Gemini to categorize a transaction based on the message and remarks.
    """

    client = _init_llm_client()

    if not client:
        return "Uncategorized"

    if categories_list is None:
        categories_list = DEFAULT_CATEGORIES

    categories_str = ", ".join(categories_list)
    prompt = f"""
    You are a financial assistant. Categorize the following transaction into one of these categories: {categories_str} using
    information from the message (e.g., recipient name, time and remarks).
    
    Transaction Message: "{message}"
    
    Return ONLY the category name. If you are unsure, return "Other".
    """

    logger.info(f"LLM categorization prompt: {prompt}")

    try:
        response = client.models.generate_content(
            model=LLM_MODEL,
            contents=prompt
        )
        category = response.text.strip() if response and response.text else "Other"
        logger.info(f"LLM categorization response: {category}")

        if category in categories_list:
            return category
        return "Other"
    except Exception as e:
        logger.error(f"Error during LLM categorization: {e}")
        return "Uncategorized"
    
def llm_parse_bank_message(message: str, transaction_type: List[str] = []) -> Tuple[Dict[str, str], Optional[str]]:
    """
    Uses Gemini to parse transaction details from a bank message.
    Returns a dictionary with keys: type, amount, description, account, timestamp
    """

    client = _init_llm_client()

    if not client:
        return {}, "LLM client not initialized"

    prompt = f"""
    You are a financial assistant. Parse the following bank message and extract the following details if it is a transaction:
    - type: str (standardized transaction type, one of {transaction_type})
    - amount: float (signed, negative for expense, positive for income)
    - description: str (merchant, recipient)
    - account: str (account or card number/identifier)
    - timestamp: datetime (optional, parsed from message, ISO8601. If time or date is not available, set to this field to null)

    Bank Message: "{message}"

    Return only the details in JSON format based on the above keys. If for optional fields you cannot find the information, set them to null.
    If the message does not describe a transaction, return "ERROR: Not a transaction.".
    If you cannot parse the message, return "ERROR: Unable to parse message.".
    If non-optional fields cannot be determined, return "ERROR: " followed by stating which fields are missing.
    Do not format the response using markdown or code blocks.
    """
    logger.info(f"LLM parsing prompt: {prompt}")

    try:
        response = client.models.generate_content(
            model=LLM_MODEL,
            contents=prompt
        )
        parsed_data = response.text.strip() if response and response.text else "{}"
        logger.info(f"LLM parsing response: {parsed_data}")

        if parsed_data.startswith("ERROR:"):
            return {}, parsed_data

        import json
        parsed_dict = json.loads(parsed_data)
        if not parsed_dict:
            return {}, "LLM failed to respond with valid data"
        return parsed_dict, None
    
    except Exception as e:
        logger.error(f"Error during LLM parsing: {e}")
        return {}, "LLM parsing error"

from typing import Dict, List, Optional, Tuple, Any
from google import genai
from src.config import GOOGLE_API_KEY, DEFAULT_CATEGORIES, LLM_MODEL
import logging
import json

logger = logging.getLogger(__name__)

def _init_llm_client(api_key: Optional[str] = None, model: str = LLM_MODEL):
    # Prefer passed api_key, fall back to global config
    key_to_use = api_key if api_key else GOOGLE_API_KEY

    if key_to_use:
        try:
            client = genai.Client(api_key=key_to_use)
            return client
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {e}")
            return None
    else:
        logger.warning("GOOGLE_API_KEY not set (neither per-user nor global). LLM features disabled.")
        return None

def categorize_transaction(message: str, categories_list: Optional[List] = None, api_key: Optional[str] = None) -> str:
    """
    Uses Gemini to categorize a transaction based on the message and remarks.
    """

    client = _init_llm_client(api_key=api_key)

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

    try:
        response = client.models.generate_content(
            model=LLM_MODEL,
            contents=prompt
        )
        category = response.text.strip() if response and response.text else "Other"

        if category in categories_list:
            return category
        return "Other"
    except Exception as e:
        logger.error(f"Error during LLM categorization: {e}")
        return "Uncategorized"
    
def llm_parse_bank_message(message: str, transaction_type: List[str] = [], api_key: Optional[str] = None) -> Tuple[Dict[str, str], Optional[str]]:
    """
    Uses Gemini to parse transaction details from a bank message.
    """

    client = _init_llm_client(api_key=api_key)

    if not client:
        return {}, "LLM client not initialized (missing API key)"

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

    try:
        response = client.models.generate_content(
            model=LLM_MODEL,
            contents=prompt
        )
        parsed_data = response.text.strip() if response and response.text else "{}"

        if parsed_data.startswith("ERROR:"):
            return {}, parsed_data

        parsed_dict = json.loads(parsed_data)
        if not parsed_dict:
            return {}, "LLM failed to respond with valid data"
        return parsed_dict, None
    
    except Exception as e:
        logger.error(f"Error during LLM parsing: {e}")
        return {}, "LLM parsing error"

def analyze_spending_habits(prompt_user: str, context_data: Dict[str, Any], api_key: Optional[str] = None) -> str:
    """
    Analyzes spending habits based on user prompt and aggregated context data.
    context_data: { "stats": ..., "transactions_sample": ... }
    """
    client = _init_llm_client(api_key=api_key)

    if not client:
        return "AI analysis unavailable. Please check your API Key settings."

    # Summarize context to avoid hitting token limits
    stats = context_data.get("stats", {})
    breakdown = stats.get("breakdown", {})
    income = stats.get("income", 0)
    expense = stats.get("expense", 0)

    # Sort breakdown
    sorted_breakdown = sorted(breakdown.items(), key=lambda x: abs(x[1]), reverse=True)
    breakdown_str = "\n".join([f"- {k}: {v:.2f}" for k, v in sorted_breakdown])

    context_str = f"""
    Total Income: {income:.2f}
    Total Expense: {expense:.2f}
    Category Breakdown:
    {breakdown_str}
    """

    full_prompt = f"""
    You are a personal finance assistant. Analyze the user's spending data and answer their question.

    Spending Context (Current Period):
    {context_str}

    User Question/Prompt: "{prompt_user}"

    Provide a helpful, insightful, and concise response. Use markdown formatting.
    """

    try:
        response = client.models.generate_content(
            model=LLM_MODEL,
            contents=full_prompt
        )
        return response.text if response and response.text else "No response generated."
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        return f"Error generating analysis: {str(e)}"

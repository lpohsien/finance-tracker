from google import genai
from src.config import GOOGLE_API_KEY, DEFAULT_CATEGORIES, LLM_MODEL
import logging

logger = logging.getLogger(__name__)

def categorize_transaction(message: str) -> str:
    """
    Uses Gemini to categorize a transaction based on the message and remarks.
    """

    if GOOGLE_API_KEY:
        client = genai.Client(api_key=GOOGLE_API_KEY)
    else:
        logger.warning("GOOGLE_API_KEY not set. LLM categorization will be disabled.")
        client = None

    if not client:
        return "Uncategorized"

    categories_str = ", ".join(DEFAULT_CATEGORIES)
    prompt = f"""
    You are a financial assistant. Categorize the following transaction into one of these categories: {categories_str} using
    information from the message (e.g., merchant name, time and remarks).
    
    Transaction Message: "{message}"
    
    Return ONLY the category name. If you are unsure, return "Other".
    """

    print(f"LLM categorization prompt: {prompt}")

    try:
        response = client.models.generate_content(
            model=LLM_MODEL,
            contents=prompt
        )
        category = response.text.strip()
        print(f"LLM categorization response: {category}")


        if category in DEFAULT_CATEGORIES:
            return category
        return "Other"
    except Exception as e:
        logger.error(f"Error during LLM categorization: {e}")
        return "Uncategorized"

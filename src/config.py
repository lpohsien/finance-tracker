import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
START_KEY = os.getenv("START_KEY")
ALLOWED_USER_IDS = [int(uid.strip()) for uid in os.getenv("ALLOWED_USER_IDS", "").split(",") if uid.strip()]

# Google Gemini Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
LLM_MODEL = "gemini-3-flash-preview"

# Storage Configuration
TRANSACTIONS_DIR = DATA_DIR

# Export Configuration
EXPORTS_DIR = DATA_DIR / "exports"

# Analytics Configuration
BIG_TICKET_THRESHOLD = 100.0

# Budget Configuration (Simple in-memory or file-based for MVP, can be extended)
# Format: {"Category": limit}
DEFAULT_BUDGETS = {
    "Total": 1000.0,
} 

# Categories
DEFAULT_CATEGORIES = [
    "Food",
    "Snack",
    "Transport",
    "Shopping",
    "Groceries",
    "Donation",
    "Entertainment",
    "Travel",
    "Health",
    "Education",
    "Subscription",
    "Utilities",
    "Tax",
    "Insurance",
    "Income",
    "Disbursement",
    "Other"
]

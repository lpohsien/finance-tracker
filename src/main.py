import logging
import sys
from pathlib import Path

# Add project root to sys.path to allow running as script
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.bot_interface import FinanceBot

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

if __name__ == '__main__':
    bot = FinanceBot()
    bot.run()

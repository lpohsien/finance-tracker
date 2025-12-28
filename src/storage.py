import csv
import logging
from pathlib import Path
from typing import List, Dict, Any
from src.config import TRANSACTIONS_DIR

logger = logging.getLogger(__name__)

class StorageManager:
    def __init__(self, file_path: Path = TRANSACTIONS_DIR):
        self.file_path_root = file_path

    def _ensure_file_exists(self, file_path: Path):
        if not file_path.exists():
            if not file_path.parent.exists():
                file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp", "type", "amount", "description", "account", "category", "remarks", "raw_message"
                ])

    def save_transaction(self, transaction: Dict[str, Any], user_id: int):
        try:
            filepath = self.file_path_root / str(user_id) / "transactions.csv"
            self._ensure_file_exists(filepath)
            with open(filepath, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "timestamp", "type", "amount", "description", "account", "category", "remarks", "raw_message"
                ])
                writer.writerow(transaction)
            logger.info(f"Transaction saved: {transaction}")
        except Exception as e:
            logger.error(f"Failed to save transaction: {e}")
            raise

    def get_transactions(self, user_id: int) -> List[Dict[str, Any]]:
        transactions = []
        filepath = self.file_path_root / str(user_id) / "transactions.csv"
        if not filepath.exists():
            return transactions
            
        try:
            with open(filepath, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Convert amount to float
                    if "amount" in row:
                        row["amount"] = float(row["amount"])
                    transactions.append(row)
        except Exception as e:
            logger.error(f"Failed to read transactions: {e}")
        
        return transactions

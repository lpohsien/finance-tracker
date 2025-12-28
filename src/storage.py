import csv
import logging
from pathlib import Path
from typing import List, Dict, Any
from src.config import TRANSACTIONS_DIR

logger = logging.getLogger(__name__)

FIELDNAMES = ["id", "timestamp", "type", "amount", "description", "account", "category", "remarks", "raw_message"]

class StorageManager:
    def __init__(self, file_path: Path = TRANSACTIONS_DIR):
        self.file_path_root = file_path

    def _ensure_file_exists(self, file_path: Path):
        if not file_path.exists():
            if not file_path.parent.exists():
                file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(FIELDNAMES)

    def save_transaction(self, transaction: Dict[str, Any], user_id: int):
        try:
            filepath = self.file_path_root / str(user_id) / "transactions.csv"
            self._ensure_file_exists(filepath)
            with open(filepath, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
                writer.writerow(transaction)
            logger.info(f"Transaction saved: {transaction.get('id')}")
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

    def delete_transaction(self, transaction_id: str, user_id: int) -> bool:
        filepath = self.file_path_root / str(user_id) / "transactions.csv"
        if not filepath.exists():
            return False
        
        transactions = []
        deleted = False
        try:
            with open(filepath, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["id"] == transaction_id:
                        deleted = True
                        continue
                    transactions.append(row)
            
            if deleted:
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
                    writer.writeheader()
                    writer.writerows(transactions)
                logger.info(f"Transaction {transaction_id} deleted for user {user_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete transaction: {e}")
            return False

    def delete_all_transactions(self, user_id: int) -> bool:
        filepath = self.file_path_root / str(user_id) / "transactions.csv"
        if not filepath.exists():
            return False
        try:
            # Just rewrite with header
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(FIELDNAMES)
            logger.info(f"All transactions deleted for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete all transactions: {e}")
            return False

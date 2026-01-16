import csv
import logging
import json
from pathlib import Path
from dataclasses import fields
import tempfile
from typing import List, Dict, Any, Optional
from src.config import TRANSACTIONS_DIR, DEFAULT_BUDGETS, BIG_TICKET_THRESHOLD, DEFAULT_CATEGORIES, DEFAULT_KEYWORDS
from src.models import TransactionData

logger = logging.getLogger(__name__)

FIELDNAMES = ["id", "timestamp", "bank", "type", "amount", "description", "account", "category", "raw_message", "status"]

assert set(FIELDNAMES) == {f.name for f in fields(TransactionData)}, "FIELDNAMES must match TransactionData fields"

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

    def _get_config_path(self, user_id: int) -> Path:
        return self.file_path_root / str(user_id) / "config.json"

    def initialize_user_config(self, user_id: int):
        config_path = self._get_config_path(user_id)
        if not config_path.exists():
            if not config_path.parent.exists():
                config_path.parent.mkdir(parents=True, exist_ok=True)
            
            initial_config = {
                "budgets": DEFAULT_BUDGETS.copy(),
                "big_ticket_threshold": BIG_TICKET_THRESHOLD,
                "categories": DEFAULT_CATEGORIES.copy(),
                "keywords": DEFAULT_KEYWORDS.copy()
            }
            self.save_user_config(user_id, initial_config)
            logger.info(f"Initialized config for user {user_id}")
            
    def _migrate_keywords(self, user_id: int, config: Dict[str, Any]):
        # Lazy migration for existing users
        logger.info(f"Migrating keywords for user {user_id}")
        keywords = DEFAULT_KEYWORDS.copy()
        user_categories = config.get("categories", DEFAULT_CATEGORIES.copy())
        for cat in user_categories:
            if cat not in keywords:
                keywords[cat] = [cat.lower()]
        config["keywords"] = keywords
        self.save_user_config(user_id, config)

    def save_user_config(self, user_id: int, config: Dict[str, Any]):
        config_path = self._get_config_path(user_id)
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save user config: {e}")

    def get_user_config(self, user_id: int) -> Dict[str, Any]:
        config_path = self._get_config_path(user_id)
        if not config_path.exists():
            self.initialize_user_config(user_id)
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if "budgets" not in config:
                    config["budgets"] = DEFAULT_BUDGETS.copy()
                if "big_ticket_threshold" not in config:
                    config["big_ticket_threshold"] = BIG_TICKET_THRESHOLD
                if "categories" not in config:
                    config["categories"] = DEFAULT_CATEGORIES.copy()
                # Ensure keywords exist
                if "keywords" not in config:
                    self._migrate_keywords(user_id, config)
                return config
        except Exception as e:
            logger.error(f"Failed to load user config: {e}")
            return {
                "budgets": DEFAULT_BUDGETS.copy(), 
                "big_ticket_threshold": BIG_TICKET_THRESHOLD,
                "categories": DEFAULT_CATEGORIES.copy(),
                "keywords": DEFAULT_KEYWORDS.copy()
            }

    def get_user_categories(self, user_id: int) -> List[str]:
        config = self.get_user_config(user_id)
        return config.get("categories", DEFAULT_CATEGORIES.copy())

    def get_user_keywords(self, user_id: int) -> Dict[str, List[str]]:
        config = self.get_user_config(user_id)
        # get_user_config already handles migration via _migrate_keywords if missing
        return config.get("keywords", DEFAULT_KEYWORDS.copy())

    def add_user_keywords(self, user_id: int, category: str, keywords_to_add: List[str]) -> tuple[List[str], List[str]]:
        config = self.get_user_config(user_id)
        keywords_map = config.get("keywords", DEFAULT_KEYWORDS.copy())
        categories = config.get("categories", DEFAULT_CATEGORIES.copy())
        
        target_category = None
        for cat in categories:
            if cat.lower() == category.lower():
                target_category = cat
                break
        
        if not target_category:
            raise ValueError(f"Category '{category}' does not exist. Please add the category first using /addcat.")
            
        if target_category not in keywords_map:
            keywords_map[target_category] = [target_category.lower()]

        added = []
        errors = []
        
        # Flatten all other keywords for uniqueness check
        all_keywords = set()
        for cat, keys in keywords_map.items():
            for k in keys:
                all_keywords.add(k.lower())

        for keyword in keywords_to_add:
            k_lower = keyword.strip().lower()
            if not k_lower: continue

            if k_lower in all_keywords:
                # Check if it belongs to current category (already exists)
                if k_lower in keywords_map[target_category]:
                    errors.append(f"'{keyword}' already exists in '{target_category}'")
                else:
                    # Find which category owns it
                    owner = next((c for c, keys in keywords_map.items() if k_lower in keys), "another category")
                    errors.append(f"'{keyword}' already used in '{owner}'")
            else:
                keywords_map[target_category].append(k_lower)
                all_keywords.add(k_lower)
                added.append(keyword)
        
        config["keywords"] = keywords_map
        self.save_user_config(user_id, config)
        return added, errors

    def delete_user_keywords(self, user_id: int, category: str, keywords_to_delete: List[str]) -> tuple[List[str], List[str]]:
        config = self.get_user_config(user_id)
        keywords_map = config.get("keywords", DEFAULT_KEYWORDS.copy())
        categories = config.get("categories", DEFAULT_CATEGORIES.copy())

        target_category = None
        for cat in categories:
            if cat.lower() == category.lower():
                target_category = cat
                break
        
        if not target_category:
            raise ValueError(f"Category '{category}' does not exist. Please add the category first using /addcat.")
            
        if target_category not in keywords_map:
            # Should not happen if initialized correctly
            keywords_map[target_category] = [target_category.lower()]
            
        deleted = []
        errors = []
        
        current_keys = keywords_map[target_category]
        
        for keyword in keywords_to_delete:
            k_lower = keyword.strip().lower()
            
            # Constraint 1: Cannot delete category name
            if k_lower == target_category.lower():
                errors.append(f"Cannot delete category name '{keyword}'")
                continue
                
            if k_lower in current_keys:
                current_keys.remove(k_lower)
                deleted.append(keyword)
            else:
                errors.append(f"'{keyword}' not found in '{target_category}'")

        config["keywords"] = keywords_map
        self.save_user_config(user_id, config)
        return deleted, errors

    def update_user_budget(self, user_id: int, category: str, amount: float):
        config = self.get_user_config(user_id)
        
        if category == "big_ticket":
            config["big_ticket_threshold"] = amount
        else:
            if "budgets" not in config:
                config["budgets"] = DEFAULT_BUDGETS.copy()
            config["budgets"][category] = amount
        
        self.save_user_config(user_id, config)

    def reset_user_budget(self, user_id: int):
        config = self.get_user_config(user_id)
        config["budgets"] = DEFAULT_BUDGETS.copy()
        config["big_ticket_threshold"] = BIG_TICKET_THRESHOLD
        self.save_user_config(user_id, config)

    def add_user_categories(self, user_id: int, categories: List[str]):
        config = self.get_user_config(user_id)
        current_categories = set(config.get("categories", DEFAULT_CATEGORIES.copy()))
        for cat in categories:
            current_categories.add(cat.strip())
        config["categories"] = list(current_categories)
        self.save_user_config(user_id, config)

    def delete_user_categories(self, user_id: int, categories: List[str]):
        config = self.get_user_config(user_id)
        current_categories = set(config.get("categories", DEFAULT_CATEGORIES.copy()))
        for cat in categories:
            current_categories.discard(cat.strip())
        config["categories"] = list(current_categories)
        self.save_user_config(user_id, config)

    def reset_user_categories(self, user_id: int):
        config = self.get_user_config(user_id)
        config["categories"] = DEFAULT_CATEGORIES.copy()
        self.save_user_config(user_id, config)

    def get_user_categories(self, user_id: int) -> List[str]:
        config = self.get_user_config(user_id)
        return config.get("categories", DEFAULT_CATEGORIES.copy())

    def save_transaction(self, transaction: TransactionData, user_id: int):
        try:
            filepath = self.file_path_root / str(user_id) / "transactions.csv"
            self._ensure_file_exists(filepath)

            transaction_dict = transaction.to_dict()

            with open(filepath, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
                writer.writerow(transaction_dict)
            logger.info(f"Transaction saved: {transaction_dict.get('id')}")
        except Exception as e:
            logger.error(f"Failed to save transaction: {e}")
            raise

    def get_transactions(self, user_id: int) -> List[TransactionData]:
        transactions = []
        filepath = self.file_path_root / str(user_id) / "transactions.csv"
        if not filepath.exists():
            return transactions
            
        try:
            with open(filepath, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                valid_fields = {f.name for f in fields(TransactionData)}
                for row in reader:
                    # Filter keys and strict validation
                    data = {k: v for k, v in row.items() if k in valid_fields}

                    # Ensure numeric fields are correctly typed before constructing TransactionData
                    if "amount" in data and data["amount"] not in (None, ""):
                        try:
                            data["amount"] = float(data["amount"])
                        except (TypeError, ValueError):
                            logger.warning(f"Skipping transaction with non-numeric amount: {row}")
                            continue
                    try:
                        transactions.append(TransactionData(**data))
                    except (TypeError, ValueError) as e:
                        logger.warning(f"Skipping invalid transaction row: {row} - {e}")
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
        
    def export_transactions(self, transactions: List[TransactionData]) -> str:
        # Create a temporary CSV file
        transactions_list = [t.to_dict() for t in transactions]
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
            writer.writerows(transactions_list)
            temp_path = f.name
        return temp_path
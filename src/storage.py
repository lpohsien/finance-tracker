import logging
import json
import uuid
import tempfile
import csv
from copy import deepcopy
from typing import List, Dict, Any, Optional
from pathlib import Path
from dateutil import parser as date_parser
from sqlalchemy.orm import Session
from sqlalchemy import delete

from src.config import DEFAULT_BUDGETS, BIG_TICKET_THRESHOLD, DEFAULT_CATEGORIES, DEFAULT_KEYWORDS
from src.models import TransactionData
from api.db import SessionLocal
from api.models import User, UserConfiguration, Transaction as DBTransaction
from src.security import get_password_hash

logger = logging.getLogger(__name__)

# Legacy fieldnames for export compatibility
FIELDNAMES = ["id", "timestamp", "bank", "type", "amount", "description", "account", "category", "raw_message", "status"]

class StorageManager:
    def __init__(self, file_path: Optional[Path] = None):
        # file_path arg is deprecated but kept for signature compatibility
        pass

    def _get_db(self):
        return SessionLocal()

    def _get_user(self, db: Session, user_identifier: Any) -> User:
        """
        Resolves a user from identifier.
        If user_identifier is a User object, returns it.
        If int, assumes it is a telegram_id (for bot backward compatibility).
        """
        if isinstance(user_identifier, User):
             # Refresh if needed or just return
             if user_identifier not in db:
                 return db.merge(user_identifier)
             return user_identifier

        # Assume telegram_id
        telegram_id = user_identifier
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            # Create shadow user
            # Username must be unique. using tg_{id}
            username = f"tg_{telegram_id}"
            # Check if username exists (unlikely unless collision)
            if db.query(User).filter(User.username == username).first():
                username = f"tg_{telegram_id}_{uuid.uuid4().hex[:4]}"
            
            # Temporary password
            temp_password = "migrated_user_change_me"

            user = User(
                username=username,
                password_hash=get_password_hash(temp_password),
                telegram_id=telegram_id
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            # Initialize config
            self._initialize_user_config_db(db, user)
            logger.info(f"Created shadow user for telegram_id {telegram_id}: {user.username}")
        
        return user

    def _initialize_user_config_db(self, db: Session, user: User):
        config = UserConfiguration(
            user_id=user.id,
            budgets=deepcopy(DEFAULT_BUDGETS),
            categories=deepcopy(DEFAULT_CATEGORIES),
            keywords=deepcopy(DEFAULT_KEYWORDS),
            big_ticket_threshold=BIG_TICKET_THRESHOLD
        )
        db.add(config)
        db.commit()

    def initialize_user_config(self, user_id: Any):
        # user_id can be telegram_id or User object
        with self._get_db() as db:
            user = self._get_user(db, user_id)
            if not user.configuration:
                self._initialize_user_config_db(db, user)

    def get_user_config(self, user_id: Any) -> Dict[str, Any]:
        with self._get_db() as db:
            user = self._get_user(db, user_id)
            if not user.configuration:
                self._initialize_user_config_db(db, user)
                db.refresh(user)

            config = user.configuration

            # Construct the legacy config dictionary structure
            return {
                "budgets": config.budgets,
                "big_ticket_threshold": config.big_ticket_threshold,
                "categories": config.categories,
                "keywords": config.keywords
            }

    def save_user_config(self, user_id: Any, config_dict: Dict[str, Any]):
        with self._get_db() as db:
            user = self._get_user(db, user_id)
            config = user.configuration
            if not config:
                self._initialize_user_config_db(db, user)
                db.refresh(user)
                config = user.configuration

            # Update fields
            if "budgets" in config_dict:
                config.budgets = config_dict["budgets"]
            if "categories" in config_dict:
                config.categories = config_dict["categories"]
            if "keywords" in config_dict:
                config.keywords = config_dict["keywords"]
            if "big_ticket_threshold" in config_dict:
                config.big_ticket_threshold = config_dict["big_ticket_threshold"]

            # Flag modified for JSON fields to ensure SQLAlchemy updates them
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(config, "budgets")
            flag_modified(config, "categories")
            flag_modified(config, "keywords")

            db.commit()

    # The following wrapper methods maintain compatibility by calling get_user_config/save_user_config
    # which now interact with the DB.

    def get_user_categories(self, user_id: int) -> List[str]:
        config = self.get_user_config(user_id)
        return config.get("categories", deepcopy(DEFAULT_CATEGORIES))

    def get_user_keywords(self, user_id: int) -> Dict[str, List[str]]:
        config = self.get_user_config(user_id)
        return config.get("keywords", deepcopy(DEFAULT_KEYWORDS))

    def add_user_keywords(self, user_id: int, category: str, keywords_to_add: List[str]) -> tuple[List[str], List[str]]:
        config = self.get_user_config(user_id)
        keywords_map = config["keywords"]
        categories = config["categories"]
        keywords_to_add_set = {k.strip().lower() for k in keywords_to_add if k.strip()}
        
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
                all_keywords.add(k)

        for keyword in keywords_to_add_set:
            k_lower = keyword.strip().lower()
            if not k_lower: continue

            if k_lower in all_keywords:
                if k_lower in keywords_map[target_category]:
                    errors.append(f"'{keyword}' already exists in category '{target_category}'")
                else:
                    owner = next((c for c, keys in keywords_map.items() if k_lower in keys), "another category")
                    errors.append(f"'{keyword}' already exists in category '{owner}'")
            else:
                keywords_map[target_category].append(k_lower)
                all_keywords.add(k_lower)
                added.append(k_lower)
        
        config["keywords"] = keywords_map
        self.save_user_config(user_id, config)
        return added, errors

    def delete_user_keywords(self, user_id: int, category: str, keywords_to_delete: List[str]) -> tuple[List[str], List[str]]:
        config = self.get_user_config(user_id)
        keywords_map = config["keywords"]
        categories = config["categories"]
        keywords_to_delete_set = {k.strip().lower() for k in keywords_to_delete if k.strip()}

        target_category = None
        for cat in categories:
            if cat.lower() == category.lower():
                target_category = cat
                break
        
        if not target_category:
            raise ValueError(f"Category '{category}' does not exist. Please add the category first using /addcat.")
            
        deleted = []
        errors = []
        
        if target_category in keywords_map:
            current_keys = keywords_map[target_category]
            for keyword in keywords_to_delete_set:
                k_lower = keyword.strip().lower()
                if k_lower == target_category.lower():
                    errors.append(f"Cannot delete category name '{keyword}'")
                    continue

                if k_lower in current_keys:
                    current_keys.remove(k_lower)
                    deleted.append(k_lower)
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
            config["budgets"][category] = amount
        self.save_user_config(user_id, config)

    def reset_user_budget(self, user_id: int):
        config = self.get_user_config(user_id)
        config["budgets"] = deepcopy(DEFAULT_BUDGETS)
        config["big_ticket_threshold"] = BIG_TICKET_THRESHOLD
        self.save_user_config(user_id, config)

    def add_user_categories(self, user_id: int, categories: List[str]) -> tuple[List[str], List[str]]:
        config = self.get_user_config(user_id)
        current_categories = set(config["categories"])
        added = []
        errors = []
        
        for cat in categories:
            cat_lower = cat.strip().lower()
            if not cat_lower: continue
            if cat_lower in current_categories:
                errors.append(f"Category '{cat}' already exists.")
            else:
                current_categories.add(cat_lower)
                if cat_lower not in config["keywords"]:
                    config["keywords"][cat_lower] = [cat_lower]
                added.append(cat_lower)
                
        config["categories"] = list(current_categories)
        self.save_user_config(user_id, config)
        return added, errors

    def delete_user_categories(self, user_id: int, categories: List[str]) -> tuple[List[str], List[str]]:
        config = self.get_user_config(user_id)
        current_categories = set(config["categories"])
        default_categories_lower = {c.lower() for c in DEFAULT_CATEGORIES}
        deleted = []
        errors = []
        
        for cat in categories:
            cat_lower = cat.strip().lower()
            if not cat_lower: continue
            if cat_lower not in current_categories:
                errors.append(f"Category '{cat}' not found.")
                continue
            if cat_lower in default_categories_lower:
                errors.append(f"Cannot delete default category '{cat}'.")
                continue
            
            current_categories.discard(cat_lower)
            if cat_lower in config["keywords"]:
                del config["keywords"][cat_lower]
            deleted.append(cat_lower)
            
        config["categories"] = list(current_categories)
        self.save_user_config(user_id, config)
        return deleted, errors

    def reset_user_categories(self, user_id: int):
        config = self.get_user_config(user_id)
        config["categories"] = [cat.lower() for cat in deepcopy(DEFAULT_CATEGORIES)]
        config["keywords"] = deepcopy(DEFAULT_KEYWORDS)
        self.save_user_config(user_id, config)

    def save_transaction(self, transaction: TransactionData, user_id: Any):
        with self._get_db() as db:
            user = self._get_user(db, user_id)
            
            # Convert TransactionData to DBTransaction
            try:
                ts = date_parser.isoparse(transaction.timestamp)
            except Exception:
                # Should not happen as validated in TransactionData
                logger.error(f"Invalid timestamp in save_transaction: {transaction.timestamp}")
                raise ValueError("Invalid timestamp")

            db_tx = DBTransaction(
                id=transaction.id,
                user_id=user.id,
                timestamp=ts,
                bank=transaction.bank,
                type=transaction.type,
                amount=transaction.amount,
                description=transaction.description,
                category=transaction.category,
                account=transaction.account,
                raw_message=transaction.raw_message,
                status=transaction.status
            )
            db.merge(db_tx) # merge to allow updates if ID exists (though ID is UUID usually)
            db.commit()
            logger.info(f"Transaction saved: {transaction.id}")

    def get_transactions(self, user_id: Any) -> List[TransactionData]:
        with self._get_db() as db:
            user = self._get_user(db, user_id)
            db_txs = db.query(DBTransaction).filter(DBTransaction.user_id == user.id).all()
            
            transactions = []
            for tx in db_txs:
                # Convert back to TransactionData
                transactions.append(TransactionData(
                    id=tx.id,
                    type=tx.type,
                    amount=tx.amount,
                    description=tx.description,
                    bank=tx.bank,
                    account=tx.account,
                    timestamp=tx.timestamp.isoformat(),
                    category=tx.category,
                    raw_message=tx.raw_message,
                    status=tx.status
                ))
            return transactions

    def delete_transaction(self, transaction_id: str, user_id: Any) -> bool:
        with self._get_db() as db:
            user = self._get_user(db, user_id)
            stmt = delete(DBTransaction).where(
                DBTransaction.id == transaction_id,
                DBTransaction.user_id == user.id
            )
            result = db.execute(stmt)
            db.commit()
            if result.rowcount > 0:
                logger.info(f"Transaction {transaction_id} deleted for user {user_id}")
                return True
            return False

    def delete_all_transactions(self, user_id: Any) -> bool:
        with self._get_db() as db:
            user = self._get_user(db, user_id)
            stmt = delete(DBTransaction).where(DBTransaction.user_id == user.id)
            db.execute(stmt)
            db.commit()
            logger.info(f"All transactions deleted for user {user_id}")
            return True

    def export_transactions(self, transactions: List[TransactionData]) -> str:
        # Create a temporary CSV file (Legacy logic preserved)
        transactions_list = [t.to_dict() for t in transactions]
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
            writer.writerows(transactions_list)
            temp_path = f.name
        return temp_path

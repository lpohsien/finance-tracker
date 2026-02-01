import os
import sys
import csv
import json
import logging
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from api.db import SessionLocal, engine, Base
from api.models import User, Transaction, UserConfiguration
from src.models import TransactionData
from src.security import get_password_hash
from dateutil import parser as date_parser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_DIR = Path("data")

def migrate_user(telegram_id: int, folder_path: Path, db):
    # 1. Create User
    username = f"tg_{telegram_id}"
    user = db.query(User).filter(User.telegram_id == telegram_id).first()

    if not user:
        logger.info(f"Creating user for telegram_id {telegram_id}...")
        temp_password = "migrated_user_change_me"
        user = User(
            username=username,
            password_hash=get_password_hash(temp_password),
            telegram_id=telegram_id
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        logger.info(f"User {username} already exists.")

    # 2. Migrate Config
    config_path = folder_path / "config.json"
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            db_config = user.configuration
            if not db_config:
                db_config = UserConfiguration(user_id=user.id)
                db.add(db_config)

            db_config.budgets = config_data.get("budgets", {})
            db_config.categories = config_data.get("categories", [])
            db_config.keywords = config_data.get("keywords", {})
            db_config.big_ticket_threshold = config_data.get("big_ticket_threshold", 100.0)

            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(db_config, "budgets")
            flag_modified(db_config, "categories")
            flag_modified(db_config, "keywords")

            db.commit()
            logger.info("Config migrated.")
        except Exception as e:
            logger.error(f"Failed to migrate config: {e}")

    # 3. Migrate Transactions
    tx_path = folder_path / "transactions.csv"
    if tx_path.exists():
        try:
            with open(tx_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    tx_id = row.get("id")
                    if not tx_id:
                        continue

                    # Check if exists
                    existing = db.query(Transaction).filter(Transaction.id == tx_id).first()
                    if existing:
                        continue

                    # Parse timestamp
                    ts_str = row.get("timestamp")
                    try:
                        ts = date_parser.isoparse(ts_str)
                    except Exception:
                        ts = datetime.utcnow()

                    amount_str = row.get("amount")
                    try:
                        amount = float(amount_str) if amount_str else 0.0
                    except ValueError:
                        amount = 0.0

                    new_tx = Transaction(
                        id=tx_id,
                        user_id=user.id,
                        timestamp=ts,
                        bank=row.get("bank", "Unknown"),
                        type=row.get("type", "Unknown"),
                        amount=amount,
                        description=row.get("description", ""),
                        category=row.get("category", "Uncategorized"),
                        account=row.get("account", ""),
                        raw_message=row.get("raw_message"),
                        status=row.get("status")
                    )
                    db.add(new_tx)
                    count += 1

                db.commit()
                logger.info(f"Migrated {count} transactions.")
        except Exception as e:
            logger.error(f"Failed to migrate transactions: {e}")

def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        if not DATA_DIR.exists():
            logger.error("Data directory not found.")
            return

        for item in DATA_DIR.iterdir():
            if item.is_dir() and item.name.isdigit():
                telegram_id = int(item.name)
                logger.info(f"Found user folder: {telegram_id}")
                migrate_user(telegram_id, item, db)

    finally:
        db.close()

if __name__ == "__main__":
    main()

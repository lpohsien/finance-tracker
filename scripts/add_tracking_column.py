import sys
import os
sys.path.append(os.getcwd())
from api.db import engine
from sqlalchemy import text

def add_column():
    with engine.connect() as conn:
        try:
            # Check if column exists
            result = conn.execute(text("PRAGMA table_info(user_configurations)"))
            columns = [row[1] for row in result.fetchall()]
            
            if "tracking_items" not in columns:
                print("Adding tracking_items column...")
                # SQLite doesn't strictly support JSON type on ALTER TABLE for all versions
                # But it maps to TEXT.
                conn.execute(text("ALTER TABLE user_configurations ADD COLUMN tracking_items TEXT"))
                print("Column added.")
            else:
                print("Column already exists.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    add_column()

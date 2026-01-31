import sqlite3
import sys
import os

DB_PATH = "data/finance.db"

def inspect_db(db_path):
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    print(f"--- Database: {db_path} ---")
    
    for table_name in tables:
        table = table_name[0]
        print(f"\n{'='*30}")
        print(f"Table: {table}")
        print(f"{'='*30}")
        
        # Get count
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"Total Rows: {count}")
            
            # Get columns
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in cursor.fetchall()]
            print(f"Columns: {', '.join(columns)}")
            print("-" * 30)
            
            # Get first 5 rows
            cursor.execute(f"SELECT * FROM {table} LIMIT 5")
            rows = cursor.fetchall()
            if rows:
                print("First 5 rows:")
                for row in rows:
                    print(row)
            else:
                print("(Empty)")
        except sqlite3.Error as e:
            print(f"Error querying table {table}: {e}")
            
    conn.close()

if __name__ == "__main__":
    target_db = sys.argv[1] if len(sys.argv) > 1 else DB_PATH
    inspect_db(target_db)

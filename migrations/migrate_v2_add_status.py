import csv
import sys
import shutil
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.config import TRANSACTIONS_DIR
from src.storage import FIELDNAMES

def migrate():
    print(f"Scanning {TRANSACTIONS_DIR} for user data...")
    if not TRANSACTIONS_DIR.exists():
        print(f"Transactions directory {TRANSACTIONS_DIR} does not exist.")
        return

    for user_dir in TRANSACTIONS_DIR.iterdir():
        if not user_dir.is_dir():
            continue
        
        file_path = user_dir / "transactions.csv"
        if not file_path.exists():
            continue
            
        print(f"Checking {file_path}...")
        
        # Check current header
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            try:
                header = next(reader)
            except StopIteration:
                print(f"  Empty file. Skipping.")
                continue

        if "status" in header:
            print(f"  Already migrated.")
            continue
            
        print(f"  Migrating {file_path}...")
        
        # Backup
        backup_path = file_path.parent / "transactions.csv.bak"
        shutil.copy2(file_path, backup_path)
        print(f"    Backed up to {backup_path}")
        
        # Read all rows
        rows = []
        with open(file_path, 'r', encoding='utf-8') as f:
            # handle if previous header didn't have all fields causing issues?
            # DictReader will use the header as keys
            dict_reader = csv.DictReader(f)
            for row in dict_reader:
                # Add missing status field
                row["status"] = "" 
                rows.append(row)
        
        # Write back with new header
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
            for row in rows:
                # Ensure only valid fields + missing fields are handled
                # row might not have all keys if previous schema was very different
                # but we know it's missing status.
                
                # Fill default for any other new fields if any (though only status is new here)
                output_row = {field: row.get(field, "") for field in FIELDNAMES}
                writer.writerow(output_row)
                
        print(f"    Migration complete for {user_dir.name}")

if __name__ == "__main__":
    migrate()

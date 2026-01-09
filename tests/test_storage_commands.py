import unittest
import tempfile
import shutil
import csv
from pathlib import Path
from src.storage import StorageManager, FIELDNAMES

class TestStorageManagerCommands(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.storage = StorageManager(file_path=Path(self.test_dir))
        self.user_id = 12345
        self.transaction = {
            "id": "test-id-1",
            "timestamp": "2025-12-29T12:00:00",
            "type": "Expense",
            "amount": -50.0,
            "description": "Test Transaction",
            "account": "1234",
            "category": "Food",
            "raw_message": "raw"
        }
        self.storage.save_transaction(self.transaction, self.user_id)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_delete_transaction(self):
        # Verify it exists
        txs = self.storage.get_transactions(self.user_id)
        self.assertEqual(len(txs), 1)
        
        # Delete it
        result = self.storage.delete_transaction("test-id-1", self.user_id)
        self.assertTrue(result)
        
        # Verify it's gone
        txs = self.storage.get_transactions(self.user_id)
        self.assertEqual(len(txs), 0)
        
        # Try deleting again
        result = self.storage.delete_transaction("test-id-1", self.user_id)
        self.assertFalse(result)

    def test_delete_all_transactions(self):
        # Add another transaction
        tx2 = self.transaction.copy()
        tx2["id"] = "test-id-2"
        self.storage.save_transaction(tx2, self.user_id)
        
        txs = self.storage.get_transactions(self.user_id)
        self.assertEqual(len(txs), 2)
        
        # Delete all
        result = self.storage.delete_all_transactions(self.user_id)
        self.assertTrue(result)
        
        # Verify empty
        txs = self.storage.get_transactions(self.user_id)
        self.assertEqual(len(txs), 0)
        
        # Verify file still exists and has header
        filepath = Path(self.test_dir) / str(self.user_id) / "transactions.csv"
        self.assertTrue(filepath.exists())
        with open(filepath, 'r') as f:
            reader = csv.reader(f)
            header = next(reader)
            self.assertEqual(header, FIELDNAMES)

if __name__ == '__main__':
    unittest.main()

import unittest
import tempfile
import shutil
from pathlib import Path
from src.storage import StorageManager
from src.config import DEFAULT_CATEGORIES

class TestCategories(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.storage = StorageManager(file_path=Path(self.test_dir))
        self.user_id = 12345
        # Initialize config
        self.storage.initialize_user_config(self.user_id)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_add_category_success(self):
        # Adding completely new categories
        added, errors = self.storage.add_user_categories(self.user_id, ["Investing", "Crypto"])
        
        self.assertIn("investing", added)
        self.assertIn("crypto", added)
        self.assertEqual(len(errors), 0)
        
        # Verify persistence
        categories = self.storage.get_user_categories(self.user_id)
        self.assertIn("investing", categories)
        self.assertIn("crypto", categories)
        
        # Verify keyword initialization
        keywords = self.storage.get_user_keywords(self.user_id)
        self.assertIn("investing", keywords)
        self.assertEqual(keywords["investing"], ["investing"])

    def test_add_category_case_insensitive(self):
        # "Investing" vs "investing"
        added, errors = self.storage.add_user_categories(self.user_id, ["INVESTING"])
        self.assertIn("investing", added)
        
        categories = self.storage.get_user_categories(self.user_id)
        self.assertIn("investing", categories)
        # Should not have duplicate if we check case strictly on retrieval (though list is strings)
        # But let's check count
        investing_count = sum(1 for c in categories if c.lower() == "investing")
        self.assertEqual(investing_count, 1)

    def test_add_category_already_exists(self):
        # "food" is a default category
        added, errors = self.storage.add_user_categories(self.user_id, ["Food", "FOOD"])
        
        self.assertEqual(len(added), 0)
        self.assertTrue(len(errors) >= 1)
        self.assertTrue(any("'Food' already exists" in e for e in errors) or any("'FOOD' already exists" in e for e in errors))

    def test_add_mixed_valid_invalid(self):
        # "food" exists, "Gaming" is new
        added, errors = self.storage.add_user_categories(self.user_id, ["Food", "Gaming", "snack"])
        
        self.assertIn("gaming", added)
        self.assertNotIn("food", added)
        self.assertNotIn("snack", added)
        
        self.assertTrue(any("Food" in e or "food" in e for e in errors))
        self.assertTrue(any("Gaming" not in e for e in errors)) # No error for gaming

    def test_delete_category_success(self):
        # Add a custom category first
        self.storage.add_user_categories(self.user_id, ["Gaming"])
        
        # Now delete it
        deleted, errors = self.storage.delete_user_categories(self.user_id, ["Gaming"])
        self.assertIn("gaming", deleted)
        self.assertEqual(len(errors), 0)
        
        categories = self.storage.get_user_categories(self.user_id)
        self.assertNotIn("gaming", categories)
        
        # Verify keywords removed
        keywords = self.storage.get_user_keywords(self.user_id)
        self.assertNotIn("gaming", keywords)

    def test_delete_category_case_insensitive(self):
        self.storage.add_user_categories(self.user_id, ["Gaming"])
        
        # Delete using different case
        deleted, errors = self.storage.delete_user_categories(self.user_id, ["GAMING"])
        self.assertIn("gaming", deleted)
        
        categories = self.storage.get_user_categories(self.user_id)
        self.assertNotIn("gaming", categories)

    def test_delete_category_not_found(self):
        deleted, errors = self.storage.delete_user_categories(self.user_id, ["NonExistent"])
        
        self.assertEqual(len(deleted), 0)
        self.assertTrue(any("not found" in e for e in errors))

    def test_delete_default_category(self):
        # "food" is default
        deleted, errors = self.storage.delete_user_categories(self.user_id, ["food"])
        
        self.assertEqual(len(deleted), 0)
        self.assertTrue(any("Cannot delete default category" in e for e in errors))

    def test_delete_mixed(self):
        # Setup: "Gaming" exists. "Food" is default. "Alien" doesn't exist.
        self.storage.add_user_categories(self.user_id, ["Gaming"])
        
        deleted, errors = self.storage.delete_user_categories(self.user_id, ["Gaming", "Food", "Alien"])
        
        # Check deleted
        self.assertIn("gaming", deleted)
        self.assertNotIn("food", deleted)
        self.assertNotIn("alien", deleted)
        
        # Check errors
        error_str = " ".join(errors)
        self.assertTrue("Food" in error_str or "food" in error_str) # Default category error
        self.assertTrue("Alien" in error_str) # Not found error

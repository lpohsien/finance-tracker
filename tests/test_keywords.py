import unittest
import tempfile
import shutil
from pathlib import Path
from src.storage import StorageManager
from src.config import DEFAULT_KEYWORDS, DEFAULT_CATEGORIES

class TestKeywords(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.storage = StorageManager(file_path=Path(self.test_dir))
        self.user_id = 99999
        # Initialize config
        self.storage.initialize_user_config(self.user_id)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_initial_keywords(self):
        keywords = self.storage.get_user_keywords(self.user_id)
        # Check if default keywords are present
        self.assertIn("Food", keywords)
        self.assertIn("food", keywords["Food"])
        # Check case
        for cat, keys in keywords.items():
            for k in keys:
                self.assertEqual(k, k.lower())

    def test_add_keyword_success(self):
        added, errors = self.storage.add_user_keywords(self.user_id, "Food", ["yummy", "Delish"])
        self.assertIn("yummy", added)
        self.assertIn("Delish", added)
        self.assertEqual(len(errors), 0)
        
        keywords = self.storage.get_user_keywords(self.user_id)
        self.assertIn("yummy", keywords["Food"])
        self.assertIn("delish", keywords["Food"]) # Autoconverted to lower

    def test_add_keyword_duplicate_same_category(self):
        # "food" already exists in Food
        added, errors = self.storage.add_user_keywords(self.user_id, "Food", ["food", "newkey"])
        self.assertIn("newkey", added)
        self.assertNotIn("food", added)
        self.assertTrue(any("already exists" in e for e in errors))
        
    def test_add_keyword_duplicate_diff_category(self):
        # "coffee" is in Snack. Try adding to Food
        added, errors = self.storage.add_user_keywords(self.user_id, "Food", ["coffee"])
        self.assertEqual(len(added), 0)
        self.assertTrue(any("already used in" in e for e in errors))

    def test_delete_keyword_success(self):
        # "dinner" is in Food
        deleted, errors = self.storage.delete_user_keywords(self.user_id, "Food", ["DINNER"])
        self.assertIn("DINNER", deleted)
        
        keywords = self.storage.get_user_keywords(self.user_id)
        self.assertNotIn("dinner", keywords["Food"])

    def test_delete_category_name_fail(self):
        # "food" is in Food and is same as category name (case insensitive)
        deleted, errors = self.storage.delete_user_keywords(self.user_id, "Food", ["food"])
        self.assertEqual(len(deleted), 0)
        self.assertTrue(any("Cannot delete category name" in e for e in errors))

    def test_delete_nonexistent_keyword(self):
        deleted, errors = self.storage.delete_user_keywords(self.user_id, "Food", ["spaceship"])
        self.assertEqual(len(deleted), 0)
        self.assertTrue(any("not found" in e for e in errors))

    def test_nonexistent_category(self):
        with self.assertRaises(ValueError):
            self.storage.add_user_keywords(self.user_id, "NonExistentCat", ["key"])
            
        with self.assertRaises(ValueError):
            self.storage.delete_user_keywords(self.user_id, "NonExistentCat", ["key"])

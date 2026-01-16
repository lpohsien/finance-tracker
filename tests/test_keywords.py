import unittest
import tempfile
import shutil
from pathlib import Path
from src.storage import StorageManager

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
        self.assertIn("food", keywords)
        self.assertIn("food", keywords["food"])
        # Check case
        for cat, keys in keywords.items():
            for k in keys:
                self.assertEqual(k, k.lower())

    def test_add_keyword_success(self):
        added, errors = self.storage.add_user_keywords(self.user_id, "Food", ["yummy", "Delish"])
        self.assertIn("yummy", added)
        self.assertIn("delish", added)
        self.assertEqual(len(errors), 0)
        
        keywords = self.storage.get_user_keywords(self.user_id)
        self.assertIn("yummy", keywords["food"])
        self.assertIn("delish", keywords["food"]) # Autoconverted to lower

    def test_ignore_duplicate_keywords_of_different_case(self):
        # "snack" already exists in Snack, "Chips" will be ignored as it is same as "chips"
        added, errors = self.storage.add_user_keywords(self.user_id, "Snack", ["SNACK", "chips", "Chips"])
        self.assertIn("chips", added)
        self.assertNotIn("SNACK", added) # ignore same keyword different case
        self.assertNotIn("Chips", added) # ignore new same keyword different case

        self.assertTrue(any("already exists" in e for e in errors)) # warns about existing same keyword
        self.assertTrue(not any("chips" in e for e in errors)) # ignore new same keyword different case
        
        keywords = self.storage.get_user_keywords(self.user_id)
        self.assertIn("chips", keywords["snack"])
        self.assertIn("snack", keywords["snack"])  # original

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
        self.assertTrue(any("already exists in category" in e for e in errors))

    def test_add_keyword_some_invalid(self):
        # "snack" exists in Snack, "treat" is new
        _, _ = self.storage.add_user_keywords(self.user_id, "snack", ["snack", "treat", "candy"])
        added, errors = self.storage.add_user_keywords(self.user_id, "food", ["treat", "mcdonalds", "candy", "pasta", "snack"])

        # "mcdonalds", "pasta" should be added
        self.assertIn("mcdonalds", added)
        self.assertIn("pasta", added)

        # "treat", "candy", "snack" should error
        errors = set(errors)
        print(errors)
        self.assertTrue("'candy' already exists in category 'snack'" in errors)
        self.assertTrue("'treat' already exists in category 'snack'" in errors)
        self.assertTrue("'snack' already exists in category 'snack'" in errors)

    def test_delete_keyword_success(self):
        # "dinner" is in Food
        deleted, errors = self.storage.delete_user_keywords(self.user_id, "Food", ["DINNER"])
        self.assertIn("dinner", deleted)
        
        keywords = self.storage.get_user_keywords(self.user_id)
        self.assertNotIn("dinner", keywords["food"])

    def test_delete_category_name_fail(self):
        # "food" is in Food and is same as category name (case insensitive)
        deleted, errors = self.storage.delete_user_keywords(self.user_id, "Food", ["food"])
        self.assertEqual(len(deleted), 0)
        self.assertTrue(any("Cannot delete category name" in e for e in errors))

    def test_delete_keyword_some_invalid(self):
        # "lunch" exists, "brunch" does not
        _, _ = self.storage.add_user_keywords(self.user_id, "Food", ["lunch", "breakfast"])
        deleted, errors = self.storage.delete_user_keywords(self.user_id, "Food", ["meal", "lunch", "kebab", "breakfast", "food"])

        # “lunch", "breakfast" should be deleted
        self.assertTrue("breakfast" in deleted)
        self.assertIn("lunch", deleted)

        # "meal", "dinner" should error (not found), "food" cannot delete
        self.assertIn("'meal' not found in 'food'", errors)
        self.assertIn("'kebab' not found in 'food'", errors)
        self.assertTrue("Cannot delete category name 'food'" in errors)

    def test_delete_keyword_case_insensitive(self):
        # "coffee" is in Snack
        deleted, errors = self.storage.delete_user_keywords(self.user_id, "Snack", ["COFFEE", "Coffee"])
        self.assertNotIn("COFFEE", deleted) # case insensitive delete, use lower case
        self.assertIn("coffee", deleted)
        
        keywords = self.storage.get_user_keywords(self.user_id)
        self.assertNotIn("coffee", keywords["snack"])
        self.assertTrue(not any("not found" in e for e in errors)) # ignore duplicate of the same word in same request

    def test_delete_nonexistent_keyword(self):
        deleted, errors = self.storage.delete_user_keywords(self.user_id, "Food", ["spaceship"])
        self.assertEqual(len(deleted), 0)
        self.assertTrue(any("not found" in e for e in errors))

    def test_nonexistent_category(self):
        with self.assertRaises(ValueError):
            self.storage.add_user_keywords(self.user_id, "NonExistentCat", ["key"])
            
        with self.assertRaises(ValueError):
            self.storage.delete_user_keywords(self.user_id, "NonExistentCat", ["key"])

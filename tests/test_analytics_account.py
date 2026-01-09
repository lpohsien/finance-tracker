import unittest
from src.analytics import AnalyticsEngine

class TestAnalyticsAccount(unittest.TestCase):
    def test_get_account_breakdown(self):
        transactions = [
            {"amount": -100.0, "category": "Food", "bank": "UOB", "account": "1234"},
            {"amount": -50.0, "category": "Transport", "bank": "DBS", "account": "5678"},
            {"amount": -20.0, "category": "Food", "bank": "UOB", "account": "1234"},
            {"amount": 2000.0, "category": "Salary", "bank": "UOB", "account": "1234"}, # Income, should be ignored
            {"amount": 50.0, "category": "Disbursement", "bank": "UOB", "account": "1234"}, # Disbursement, should be counted as positive expense (reduction)
        ]
        
        analytics = AnalyticsEngine(transactions)
        breakdown = analytics.get_account_breakdown()
        
        self.assertIn("UOB 1234 (Unknown)", breakdown)
        self.assertIn("DBS 5678 (Unknown)", breakdown)
        
        # Keys in analytics are f"{bank} {account} ({type})"
        # For the test data:
        # 1. bank=UOB, account=1234, type missing -> type="Unknown"
        # 2. bank=DBS, account=5678, type missing -> type="Unknown"

        # UOB 1234 (Unknown): -100 - 20 + 50 = -70
        self.assertEqual(breakdown["UOB 1234 (Unknown)"], -70.0)
        # DBS 5678 (Unknown): -50
        self.assertEqual(breakdown["DBS 5678 (Unknown)"], -50.0)

if __name__ == '__main__':
    unittest.main()

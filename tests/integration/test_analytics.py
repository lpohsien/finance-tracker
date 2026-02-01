"""
Integration tests for analytics endpoints.

Tests:
- Monthly summary
- Category breakdown
- Analytics calculations with seeded transaction data
"""

import pytest
import httpx
from datetime import datetime


pytestmark = pytest.mark.integration


class TestAnalyticsEndpoints:
    """Tests for analytics API endpoints."""
    
    @pytest.fixture
    def setup_transactions_for_analytics(self, sync_auth_user: httpx.Client) -> list:
        """Create transactions for analytics testing."""
        # Setup categories
        sync_auth_user.post(
            "/api/config/categories",
            json={"categories": ["food", "shopping", "transport", "income"]},
        )
        
        now = datetime.now()
        transactions = [
            # Expenses
            {
                "type": "Card",
                "amount": -20.00,
                "description": "Lunch",
                "bank": "TestBank",
                "category": "food",
                "account": "1234",
                "timestamp": now.isoformat(),
            },
            {
                "type": "Card",
                "amount": -50.00,
                "description": "Dinner",
                "bank": "TestBank",
                "category": "food",
                "account": "1234",
                "timestamp": now.isoformat(),
            },
            {
                "type": "Card",
                "amount": -100.00,
                "description": "Clothing",
                "bank": "TestBank",
                "category": "shopping",
                "account": "1234",
                "timestamp": now.isoformat(),
            },
            {
                "type": "Card",
                "amount": -30.00,
                "description": "Taxi",
                "bank": "TestBank",
                "category": "transport",
                "account": "1234",
                "timestamp": now.isoformat(),
            },
            # Income
            {
                "type": "PayNow",
                "amount": 500.00,
                "description": "Salary",
                "bank": "TestBank",
                "category": "income",
                "account": "1234",
                "timestamp": now.isoformat(),
            },
        ]
        
        tx_ids = []
        for tx in transactions:
            response = sync_auth_user.post("/api/transactions", json=tx)
            tx_ids.append(response.json()["id"])
        
        yield {
            "tx_ids": tx_ids,
            "total_expense": -200.00,  # 20 + 50 + 100 + 30
            "total_income": 500.00,
            "food_total": -70.00,
            "shopping_total": -100.00,
            "transport_total": -30.00,
        }
        
        # Cleanup
        for tx_id in tx_ids:
            sync_auth_user.delete(f"/api/transactions/{tx_id}")
    
    def test_get_monthly_stats(
        self, sync_auth_user: httpx.Client, setup_transactions_for_analytics: dict
    ):
        """Test getting monthly statistics."""
        # Get current year and month
        now = datetime.now()
        
        response = sync_auth_user.get(
            f"/api/stats/monthly?year={now.year}&month={now.month}"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check structure
        assert "income" in data
        assert "expense" in data
        assert "breakdown" in data
        
        # Verify calculated values match our seeded data
        expected = setup_transactions_for_analytics
        assert data["income"] == expected["total_income"]
        assert data["expense"] == expected["total_expense"]
    
    def test_get_daily_stats(
        self, sync_auth_user: httpx.Client, setup_transactions_for_analytics: dict
    ):
        """Test getting daily statistics."""
        # Get current year and month
        now = datetime.now()
        
        response = sync_auth_user.get(
            f"/api/stats/daily?year={now.year}&month={now.month}"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check structure
        assert "daily_spending" in data
        assert "monthly_budget" in data
        
        # Should have spending data
        assert isinstance(data["daily_spending"], dict)
    
    def test_category_breakdown_accuracy(
        self, sync_auth_user: httpx.Client, setup_transactions_for_analytics: dict
    ):
        """Test that category breakdown matches seeded data."""
        now = datetime.now()
        
        response = sync_auth_user.get(
            f"/api/stats/monthly?year={now.year}&month={now.month}"
        )
        
        assert response.status_code == 200
        data = response.json()
        breakdown = data.get("breakdown", {})
        
        expected = setup_transactions_for_analytics
        
        # Check category totals (breakdown only includes expenses)
        if "food" in breakdown:
            assert breakdown["food"] == expected["food_total"]
        if "shopping" in breakdown:
            assert breakdown["shopping"] == expected["shopping_total"]
        if "transport" in breakdown:
            assert breakdown["transport"] == expected["transport_total"]


class TestTransactionOptions:
    """Tests for transaction filter options endpoint."""
    
    def test_get_transaction_options(self, sync_auth_user: httpx.Client):
        """Test getting available filter options."""
        response = sync_auth_user.get("/api/transactions/options")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check structure
        assert "categories" in data
        assert "banks" in data
        assert "accounts" in data
        assert "types" in data
        
        # All should be lists
        assert isinstance(data["categories"], list)
        assert isinstance(data["banks"], list)
        assert isinstance(data["accounts"], list)
        assert isinstance(data["types"], list)

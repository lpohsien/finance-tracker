"""
Integration tests for transaction endpoints.

Tests:
- Create transaction
- Get transaction by ID
- List transactions
- Update transaction
- Delete transaction
- Transaction filtering
"""

import pytest
import httpx
from datetime import datetime, timedelta


pytestmark = pytest.mark.integration


class TestTransactionCRUD:
    """Tests for basic transaction CRUD operations."""
    
    @pytest.fixture
    def sample_transaction(self) -> dict:
        """Sample transaction data for testing."""
        return {
            "type": "Card",
            "amount": -25.50,
            "description": "Test Coffee Shop",
            "bank": "TestBank",
            "category": "food",
            "account": "1234",
            "timestamp": datetime.now().isoformat(),
        }
    
    def test_create_transaction(
        self, sync_auth_user: httpx.Client, sample_transaction: dict
    ):
        """Test creating a new transaction."""
        # First, add the category
        sync_auth_user.post(
            "/api/config/categories",
            json={"categories": ["food"]},
        )
        
        response = sync_auth_user.post(
            "/api/transactions",
            json=sample_transaction,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == sample_transaction["amount"]
        assert data["description"] == sample_transaction["description"]
        assert "id" in data
        
        # Cleanup
        sync_auth_user.delete(f"/api/transactions/{data['id']}")
    
    def test_get_transaction(
        self, sync_auth_user: httpx.Client, sample_transaction: dict
    ):
        """Test getting a transaction by ID."""
        # Setup category
        sync_auth_user.post(
            "/api/config/categories",
            json={"categories": ["food"]},
        )
        
        # Create transaction
        create_response = sync_auth_user.post(
            "/api/transactions",
            json=sample_transaction,
        )
        tx_id = create_response.json()["id"]
        
        # Get transaction
        response = sync_auth_user.get(f"/api/transactions/{tx_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == tx_id
        assert data["amount"] == sample_transaction["amount"]
        
        # Cleanup
        sync_auth_user.delete(f"/api/transactions/{tx_id}")
    
    def test_get_nonexistent_transaction(self, sync_auth_user: httpx.Client):
        """Test getting a nonexistent transaction returns 404."""
        response = sync_auth_user.get("/api/transactions/nonexistent-id-12345")
        assert response.status_code == 404
    
    def test_list_transactions(
        self, sync_auth_user: httpx.Client, sample_transaction: dict
    ):
        """Test listing transactions."""
        # Setup category
        sync_auth_user.post(
            "/api/config/categories",
            json={"categories": ["food"]},
        )
        
        # Create a transaction
        create_response = sync_auth_user.post(
            "/api/transactions",
            json=sample_transaction,
        )
        tx_id = create_response.json()["id"]
        
        # List transactions
        response = sync_auth_user.get("/api/transactions")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Find our transaction
        tx_ids = [tx["id"] for tx in data]
        assert tx_id in tx_ids
        
        # Cleanup
        sync_auth_user.delete(f"/api/transactions/{tx_id}")
    
    def test_update_transaction(
        self, sync_auth_user: httpx.Client, sample_transaction: dict
    ):
        """Test updating a transaction."""
        # Setup categories
        sync_auth_user.post(
            "/api/config/categories",
            json={"categories": ["food", "shopping"]},
        )
        
        # Create transaction
        create_response = sync_auth_user.post(
            "/api/transactions",
            json=sample_transaction,
        )
        tx_id = create_response.json()["id"]
        
        # Update transaction
        update_data = {
            "amount": -50.00,
            "description": "Updated Description",
            "category": "shopping",
        }
        
        response = sync_auth_user.put(
            f"/api/transactions/{tx_id}",
            json=update_data,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == -50.00
        assert data["description"] == "Updated Description"
        assert data["category"] == "shopping"
        
        # Cleanup
        sync_auth_user.delete(f"/api/transactions/{tx_id}")
    
    def test_delete_transaction(
        self, sync_auth_user: httpx.Client, sample_transaction: dict
    ):
        """Test deleting a transaction."""
        # Setup category
        sync_auth_user.post(
            "/api/config/categories",
            json={"categories": ["food"]},
        )
        
        # Create transaction
        create_response = sync_auth_user.post(
            "/api/transactions",
            json=sample_transaction,
        )
        tx_id = create_response.json()["id"]
        
        # Delete transaction
        response = sync_auth_user.delete(f"/api/transactions/{tx_id}")
        assert response.status_code == 200
        
        # Verify deletion
        get_response = sync_auth_user.get(f"/api/transactions/{tx_id}")
        assert get_response.status_code == 404


class TestTransactionFilters:
    """Tests for transaction filtering functionality."""
    
    @pytest.fixture
    def setup_transactions(self, sync_auth_user: httpx.Client) -> list:
        """Create multiple transactions for filter testing."""
        # Setup categories
        sync_auth_user.post(
            "/api/config/categories",
            json={"categories": ["food", "shopping", "transport"]},
        )
        
        now = datetime.now()
        transactions = [
            {
                "type": "Card",
                "amount": -10.00,
                "description": "Coffee",
                "bank": "BankA",
                "category": "food",
                "account": "1111",
                "timestamp": (now - timedelta(days=1)).isoformat(),
            },
            {
                "type": "PayNow",
                "amount": -50.00,
                "description": "Groceries",
                "bank": "BankA",
                "category": "food",
                "account": "1111",
                "timestamp": now.isoformat(),
            },
            {
                "type": "Card",
                "amount": -100.00,
                "description": "Clothing Store",
                "bank": "BankB",
                "category": "shopping",
                "account": "2222",
                "timestamp": now.isoformat(),
            },
        ]
        
        tx_ids = []
        for tx in transactions:
            response = sync_auth_user.post("/api/transactions", json=tx)
            tx_ids.append(response.json()["id"])
        
        yield tx_ids
        
        # Cleanup
        for tx_id in tx_ids:
            sync_auth_user.delete(f"/api/transactions/{tx_id}")
    
    def test_filter_by_category(
        self, sync_auth_user: httpx.Client, setup_transactions: list
    ):
        """Test filtering transactions by category."""
        response = sync_auth_user.get("/api/transactions?category=food")
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned transactions should be in food category
        for tx in data:
            assert tx["category"] == "food"
    
    def test_filter_by_bank(
        self, sync_auth_user: httpx.Client, setup_transactions: list
    ):
        """Test filtering transactions by bank."""
        response = sync_auth_user.get("/api/transactions?bank=BankA")
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned transactions should be from BankA
        for tx in data:
            assert tx["bank"] == "BankA"
    
    def test_filter_by_type(
        self, sync_auth_user: httpx.Client, setup_transactions: list
    ):
        """Test filtering transactions by type."""
        response = sync_auth_user.get("/api/transactions?type=Card")
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned transactions should be Card type
        for tx in data:
            assert tx["type"] == "Card"
    
    def test_search_transactions(
        self, sync_auth_user: httpx.Client, setup_transactions: list
    ):
        """Test searching transactions by description."""
        response = sync_auth_user.get("/api/transactions?search=Coffee")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should find the Coffee transaction
        assert len(data) >= 1
        descriptions = [tx["description"] for tx in data]
        assert any("Coffee" in desc for desc in descriptions)

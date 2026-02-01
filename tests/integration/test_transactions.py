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
        """Test updating a transaction with multiple fields."""
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
    
    def test_update_transaction_amount_only(
        self, sync_auth_user: httpx.Client, sample_transaction: dict
    ):
        """Test updating only the amount field."""
        sync_auth_user.post(
            "/api/config/categories",
            json={"categories": ["food"]},
        )
        
        create_response = sync_auth_user.post(
            "/api/transactions",
            json=sample_transaction,
        )
        tx_id = create_response.json()["id"]
        original_description = sample_transaction["description"]
        
        response = sync_auth_user.put(
            f"/api/transactions/{tx_id}",
            json={"amount": -99.99},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == -99.99
        assert data["description"] == original_description  # Unchanged
        
        sync_auth_user.delete(f"/api/transactions/{tx_id}")
    
    def test_update_transaction_description_only(
        self, sync_auth_user: httpx.Client, sample_transaction: dict
    ):
        """Test updating only the description field."""
        sync_auth_user.post(
            "/api/config/categories",
            json={"categories": ["food"]},
        )
        
        create_response = sync_auth_user.post(
            "/api/transactions",
            json=sample_transaction,
        )
        tx_id = create_response.json()["id"]
        original_amount = sample_transaction["amount"]
        
        response = sync_auth_user.put(
            f"/api/transactions/{tx_id}",
            json={"description": "New Description Only"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "New Description Only"
        assert data["amount"] == original_amount  # Unchanged
        
        sync_auth_user.delete(f"/api/transactions/{tx_id}")
    
    def test_update_transaction_category_only(
        self, sync_auth_user: httpx.Client, sample_transaction: dict
    ):
        """Test updating only the category field."""
        sync_auth_user.post(
            "/api/config/categories",
            json={"categories": ["food", "transport"]},
        )
        
        create_response = sync_auth_user.post(
            "/api/transactions",
            json=sample_transaction,
        )
        tx_id = create_response.json()["id"]
        
        response = sync_auth_user.put(
            f"/api/transactions/{tx_id}",
            json={"category": "transport"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "transport"
        
        sync_auth_user.delete(f"/api/transactions/{tx_id}")
    
    def test_update_transaction_type_only(
        self, sync_auth_user: httpx.Client, sample_transaction: dict
    ):
        """Test updating only the type field."""
        sync_auth_user.post(
            "/api/config/categories",
            json={"categories": ["food"]},
        )
        
        create_response = sync_auth_user.post(
            "/api/transactions",
            json=sample_transaction,
        )
        tx_id = create_response.json()["id"]
        
        response = sync_auth_user.put(
            f"/api/transactions/{tx_id}",
            json={"type": "PayNow"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "PayNow"
        
        sync_auth_user.delete(f"/api/transactions/{tx_id}")
    
    def test_update_transaction_bank_only(
        self, sync_auth_user: httpx.Client, sample_transaction: dict
    ):
        """Test updating only the bank field."""
        sync_auth_user.post(
            "/api/config/categories",
            json={"categories": ["food"]},
        )
        
        create_response = sync_auth_user.post(
            "/api/transactions",
            json=sample_transaction,
        )
        tx_id = create_response.json()["id"]
        
        response = sync_auth_user.put(
            f"/api/transactions/{tx_id}",
            json={"bank": "NewBank"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["bank"] == "NewBank"
        
        sync_auth_user.delete(f"/api/transactions/{tx_id}")
    
    def test_update_transaction_account_only(
        self, sync_auth_user: httpx.Client, sample_transaction: dict
    ):
        """Test updating only the account field."""
        sync_auth_user.post(
            "/api/config/categories",
            json={"categories": ["food"]},
        )
        
        create_response = sync_auth_user.post(
            "/api/transactions",
            json=sample_transaction,
        )
        tx_id = create_response.json()["id"]
        
        response = sync_auth_user.put(
            f"/api/transactions/{tx_id}",
            json={"account": "9999"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["account"] == "9999"
        
        sync_auth_user.delete(f"/api/transactions/{tx_id}")
    
    def test_update_transaction_timestamp_only(
        self, sync_auth_user: httpx.Client, sample_transaction: dict
    ):
        """Test updating only the timestamp field."""
        sync_auth_user.post(
            "/api/config/categories",
            json={"categories": ["food"]},
        )
        
        create_response = sync_auth_user.post(
            "/api/transactions",
            json=sample_transaction,
        )
        tx_id = create_response.json()["id"]
        new_timestamp = (datetime.now() - timedelta(days=5)).isoformat()
        
        response = sync_auth_user.put(
            f"/api/transactions/{tx_id}",
            json={"timestamp": new_timestamp},
        )
        
        assert response.status_code == 200
        
        sync_auth_user.delete(f"/api/transactions/{tx_id}")
    
    def test_update_transaction_type_and_amount(
        self, sync_auth_user: httpx.Client, sample_transaction: dict
    ):
        """Test updating type and amount together."""
        sync_auth_user.post(
            "/api/config/categories",
            json={"categories": ["food"]},
        )
        
        create_response = sync_auth_user.post(
            "/api/transactions",
            json=sample_transaction,
        )
        tx_id = create_response.json()["id"]
        
        response = sync_auth_user.put(
            f"/api/transactions/{tx_id}",
            json={"type": "PayNow", "amount": -75.00},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "PayNow"
        assert data["amount"] == -75.00
        
        sync_auth_user.delete(f"/api/transactions/{tx_id}")
    
    def test_update_transaction_account_and_type(
        self, sync_auth_user: httpx.Client, sample_transaction: dict
    ):
        """Test updating account and type together."""
        sync_auth_user.post(
            "/api/config/categories",
            json={"categories": ["food"]},
        )
        
        create_response = sync_auth_user.post(
            "/api/transactions",
            json=sample_transaction,
        )
        tx_id = create_response.json()["id"]
        
        response = sync_auth_user.put(
            f"/api/transactions/{tx_id}",
            json={"account": "5555", "type": "NETS QR"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["account"] == "5555"
        assert data["type"] == "NETS QR"
        
        sync_auth_user.delete(f"/api/transactions/{tx_id}")
    
    def test_update_nonexistent_transaction(self, sync_auth_user: httpx.Client):
        """Test updating a transaction that doesn't exist returns 404."""
        response = sync_auth_user.put(
            "/api/transactions/nonexistent-id-12345",
            json={"amount": -100.00},
        )
        assert response.status_code == 404
    
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
                "description": "Morning Coffee at Starbucks",
                "bank": "BankA",
                "category": "food",
                "account": "1111",
                "timestamp": (now - timedelta(days=7)).isoformat(),
            },
            {
                "type": "PayNow",
                "amount": -50.00,
                "description": "Groceries from NTUC",
                "bank": "BankA",
                "category": "food",
                "account": "1111",
                "timestamp": (now - timedelta(days=3)).isoformat(),
            },
            {
                "type": "Card",
                "amount": -100.00,
                "description": "Clothing Store Purchase",
                "bank": "BankB",
                "category": "shopping",
                "account": "2222",
                "timestamp": (now - timedelta(days=1)).isoformat(),
            },
            {
                "type": "NETS QR",
                "amount": -15.00,
                "description": "MRT Top-up",
                "bank": "BankA",
                "category": "transport",
                "account": "1111",
                "timestamp": now.isoformat(),
            },
            {
                "type": "Card",
                "amount": -200.00,
                "description": "Coffee Machine from Amazon",
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
        
        yield {
            "tx_ids": tx_ids,
            "now": now,
            "transactions": transactions,
        }
        
        # Cleanup
        for tx_id in tx_ids:
            sync_auth_user.delete(f"/api/transactions/{tx_id}")
    
    def test_filter_by_category(
        self, sync_auth_user: httpx.Client, setup_transactions: dict
    ):
        """Test filtering transactions by category."""
        response = sync_auth_user.get("/api/transactions?category=food")
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned transactions should be in food category
        assert len(data) >= 2
        for tx in data:
            assert tx["category"] == "food"
    
    def test_filter_by_bank(
        self, sync_auth_user: httpx.Client, setup_transactions: dict
    ):
        """Test filtering transactions by bank."""
        response = sync_auth_user.get("/api/transactions?bank=BankA")
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned transactions should be from BankA
        assert len(data) >= 3
        for tx in data:
            assert tx["bank"] == "BankA"
    
    def test_filter_by_type(
        self, sync_auth_user: httpx.Client, setup_transactions: dict
    ):
        """Test filtering transactions by type."""
        response = sync_auth_user.get("/api/transactions?type=Card")
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned transactions should be Card type
        assert len(data) >= 3
        for tx in data:
            assert tx["type"] == "Card"
    
    def test_filter_by_account(
        self, sync_auth_user: httpx.Client, setup_transactions: dict
    ):
        """Test filtering transactions by account."""
        response = sync_auth_user.get("/api/transactions?account=2222")
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned transactions should be from account 2222
        assert len(data) >= 2
        for tx in data:
            assert tx["account"] == "2222"
    
    def test_search_transactions(
        self, sync_auth_user: httpx.Client, setup_transactions: dict
    ):
        """Test searching transactions by description."""
        response = sync_auth_user.get("/api/transactions?search=Coffee")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should find transactions with Coffee in description
        assert len(data) >= 1
        descriptions = [tx["description"] for tx in data]
        assert all("Coffee" in desc or "coffee" in desc.lower() for desc in descriptions)
    
    def test_search_case_insensitive(
        self, sync_auth_user: httpx.Client, setup_transactions: dict
    ):
        """Test that search is case insensitive by default."""
        response = sync_auth_user.get("/api/transactions?search=coffee")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should find transactions with Coffee (case insensitive)
        assert len(data) >= 1
    
    def test_filter_by_date_range(
        self, sync_auth_user: httpx.Client, setup_transactions: dict
    ):
        """Test filtering transactions by date range."""
        now = setup_transactions["now"]
        start_date = (now - timedelta(days=2)).isoformat()
        end_date = now.isoformat()
        
        response = sync_auth_user.get(
            f"/api/transactions?start_date={start_date}&end_date={end_date}"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should only return transactions within the date range
        assert len(data) >= 2  # Transactions from last 2 days
    
    def test_filter_by_start_date_only(
        self, sync_auth_user: httpx.Client, setup_transactions: dict
    ):
        """Test filtering transactions with only start date."""
        now = setup_transactions["now"]
        start_date = (now - timedelta(days=4)).isoformat()
        
        response = sync_auth_user.get(f"/api/transactions?start_date={start_date}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return transactions from start_date onwards
        assert len(data) >= 3
    
    def test_filter_by_end_date_only(
        self, sync_auth_user: httpx.Client, setup_transactions: dict
    ):
        """Test filtering transactions with only end date."""
        now = setup_transactions["now"]
        end_date = (now - timedelta(days=2)).isoformat()
        
        response = sync_auth_user.get(f"/api/transactions?end_date={end_date}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return transactions up to end_date
        assert len(data) >= 1
    
    def test_combined_filter_category_and_bank(
        self, sync_auth_user: httpx.Client, setup_transactions: dict
    ):
        """Test filtering by both category and bank."""
        response = sync_auth_user.get("/api/transactions?category=food&bank=BankA")
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned transactions should match both filters
        assert len(data) >= 2
        for tx in data:
            assert tx["category"] == "food"
            assert tx["bank"] == "BankA"
    
    def test_combined_filter_type_and_account(
        self, sync_auth_user: httpx.Client, setup_transactions: dict
    ):
        """Test filtering by both type and account."""
        response = sync_auth_user.get("/api/transactions?type=Card&account=2222")
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned transactions should match both filters
        assert len(data) >= 2
        for tx in data:
            assert tx["type"] == "Card"
            assert tx["account"] == "2222"
    
    def test_combined_filter_date_range_and_category(
        self, sync_auth_user: httpx.Client, setup_transactions: dict
    ):
        """Test filtering by date range and category."""
        now = setup_transactions["now"]
        start_date = (now - timedelta(days=4)).isoformat()
        
        response = sync_auth_user.get(
            f"/api/transactions?start_date={start_date}&category=food"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned should match date and category
        for tx in data:
            assert tx["category"] == "food"
    
    def test_combined_filter_search_and_type(
        self, sync_auth_user: httpx.Client, setup_transactions: dict
    ):
        """Test filtering by search term and type."""
        response = sync_auth_user.get("/api/transactions?search=Coffee&type=Card")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should find Card transactions with Coffee
        for tx in data:
            assert tx["type"] == "Card"
            assert "Coffee" in tx["description"] or "coffee" in tx["description"].lower()
    
    def test_combined_filter_date_range_and_search(
        self, sync_auth_user: httpx.Client, setup_transactions: dict
    ):
        """Test filtering by date range and search term."""
        now = setup_transactions["now"]
        start_date = (now - timedelta(days=10)).isoformat()
        
        response = sync_auth_user.get(
            f"/api/transactions?start_date={start_date}&search=Starbucks"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should find Starbucks transactions in date range
        for tx in data:
            assert "Starbucks" in tx["description"]
    
    def test_triple_filter_category_bank_type(
        self, sync_auth_user: httpx.Client, setup_transactions: dict
    ):
        """Test filtering by category, bank, and type together."""
        response = sync_auth_user.get(
            "/api/transactions?category=shopping&bank=BankB&type=Card"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # All should match all three filters
        for tx in data:
            assert tx["category"] == "shopping"
            assert tx["bank"] == "BankB"
            assert tx["type"] == "Card"
    
    def test_filter_no_results(
        self, sync_auth_user: httpx.Client, setup_transactions: dict
    ):
        """Test filtering that returns no results."""
        response = sync_auth_user.get("/api/transactions?category=nonexistent")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return empty list
        assert data == []
    
    def test_filter_with_limit(
        self, sync_auth_user: httpx.Client, setup_transactions: dict
    ):
        """Test filtering with result limit."""
        response = sync_auth_user.get("/api/transactions?limit=2")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return at most 2 results
        assert len(data) <= 2
    
    def test_filter_with_offset(
        self, sync_auth_user: httpx.Client, setup_transactions: dict
    ):
        """Test filtering with offset for pagination."""
        # First get all transactions
        all_response = sync_auth_user.get("/api/transactions")
        all_data = all_response.json()
        
        if len(all_data) > 2:
            # Get with offset
            response = sync_auth_user.get("/api/transactions?offset=2&limit=10")
            
            assert response.status_code == 200
            data = response.json()
            
            # Should skip first 2 results
            assert len(data) <= len(all_data) - 2

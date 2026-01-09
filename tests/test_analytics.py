import pytest
from src.analytics import AnalyticsEngine
from src.models import TransactionData

@pytest.fixture
def sample_transactions():
    return [
        TransactionData(timestamp="2025-12-27T13:44:00", type="PayNow Outgoing", amount=-20.0, category="Food", bank="Test", description=""),
        TransactionData(timestamp="2025-12-28T10:00:00", type="PayNow Incoming", amount=100.0, category="Income", bank="Test", description=""),
        TransactionData(timestamp="2025-12-28T18:00:00", type="Card Transaction", amount=-50.0, category="Shopping", bank="Test", description=""),
        TransactionData(timestamp="2025-12-29T12:00:00", type="PayNow Outgoing", amount=-150.0, category="Food", bank="Test", description=""), # Big ticket
    ]

def test_total_income_expense(sample_transactions):
    analytics = AnalyticsEngine(sample_transactions)
    totals = analytics.get_total_income_expense()
    assert totals["income"] == 100.0
    assert totals["expense"] == -220.0

def test_category_breakdown(sample_transactions):
    analytics = AnalyticsEngine(sample_transactions)
    breakdown = analytics.get_category_breakdown()
    assert breakdown["Food"] == -170.0
    assert breakdown["Shopping"] == -50.0
    assert "Income" not in breakdown # Breakdown is for expenses usually, or we can separate. Code implements expenses only.

def test_big_ticket_expenses(sample_transactions):
    analytics = AnalyticsEngine(sample_transactions)
    big_tickets = analytics.get_big_ticket_expenses(threshold=100.0)
    assert len(big_tickets) == 1
    assert big_tickets[0].amount == -150.0

def test_budget_alerts(sample_transactions):
    # Mock budget in config or pass it?
    # The class uses DEFAULT_BUDGETS from config. 
    # We can patch it or just rely on it being empty/default.
    # Let's assume we want to test logic.
    from src import analytics
    analytics.DEFAULT_BUDGETS = {"Food": 100.0}
    
    engine = AnalyticsEngine(sample_transactions)
    alerts = engine.check_budget_alerts(sample_transactions)
    
    # Food spent is 170, limit 100 -> 170% -> Exceeded
    assert any("Budget Exceeded for Food" in alert for alert in alerts)

def test_budget_alerts_custom_budget(sample_transactions):
    engine = AnalyticsEngine(sample_transactions)
    custom_budgets = {"Food": 200.0}
    # Food spent is 170, limit 200 -> 85% -> 75% Alert
    alerts = engine.check_budget_alerts(sample_transactions, budgets=custom_budgets)
    assert any("75% Budget Alert for Food" in alert for alert in alerts)
    assert not any("Budget Exceeded for Food" in alert for alert in alerts)

def test_daily_breakdown(sample_transactions):
    analytics = AnalyticsEngine(sample_transactions)
    breakdown = analytics.get_daily_breakdown()
    
    # 27th: 20
    # 28th: 50 (Income ignored)
    # 29th: 150
    
    assert breakdown[27] == 20.0
    assert breakdown[28] == 50.0
    assert breakdown[29] == 150.0
    assert 30 not in breakdown


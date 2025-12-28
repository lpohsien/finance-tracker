from typing import List, Dict, Any
from datetime import datetime
from collections import defaultdict
from src.config import BIG_TICKET_THRESHOLD, DEFAULT_BUDGETS

class AnalyticsEngine:
    def __init__(self, transactions: List[Dict[str, Any]]):
        self.transactions = transactions

    def get_total_income_expense(self) -> Dict[str, float]:
        income = sum(t["amount"] for t in self.transactions if t["amount"] > 0)
        expense = sum(t["amount"] for t in self.transactions if t["amount"] < 0)
        return {"income": income, "expense": expense}

    def get_category_breakdown(self) -> Dict[str, float]:
        breakdown = defaultdict(float)
        for t in self.transactions:
            if t["amount"] < 0: # Only expenses
                breakdown[t["category"]] += abs(t["amount"])
        return dict(breakdown)

    def get_big_ticket_expenses(self, threshold: float = BIG_TICKET_THRESHOLD) -> List[Dict[str, Any]]:
        return [t for t in self.transactions if t["amount"] < 0 and abs(t["amount"]) >= threshold]

    def check_budget_alerts(self, current_month_transactions: List[Dict[str, Any]]) -> List[str]:
        category_spend = defaultdict(float)
        category_spend["Total"] = 0.0
        for t in current_month_transactions:
            if t["amount"] < 0:
                category_spend[t["category"]] += abs(t["amount"])
                category_spend["Total"] += abs(t["amount"])
        
        total_expenses_str = f"${category_spend['Total']:.2f} / ${DEFAULT_BUDGETS.get('Total', 0):.2f}"
        total_expenses_ratio_str = f"{(category_spend['Total'] / DEFAULT_BUDGETS.get('Total', 1)) * 100:.2f}%"
        alerts = [f"📊 Monthly Expenses: \n {total_expenses_str} ({total_expenses_ratio_str})"]


        for category, limit in DEFAULT_BUDGETS.items():
            spent = category_spend.get(category, 0)
            if limit > 0:
                percentage = (spent / limit) * 100
                if percentage >= 100:
                    alerts.append(f"🚨 Budget Exceeded for {category}: ${spent:.2f} / ${limit:.2f}")
                elif percentage >= 90:
                    alerts.append(f"⚠️ 90% Budget Alert for {category}: ${spent:.2f} / ${limit:.2f}")
                elif percentage >= 75:
                    alerts.append(f"⚠️ 75% Budget Alert for {category}: ${spent:.2f} / ${limit:.2f}")
                elif percentage >= 50:
                    alerts.append(f"ℹ️ 50% Budget Alert for {category}: ${spent:.2f} / ${limit:.2f}")
        return alerts

    def filter_transactions_by_month(self, year: int, month: int) -> List[Dict[str, Any]]:
        filtered = []
        for t in self.transactions:
            try:
                dt = datetime.fromisoformat(t["timestamp"])
                if dt.year == year and dt.month == month:
                    filtered.append(t)
            except ValueError:
                continue
        return filtered

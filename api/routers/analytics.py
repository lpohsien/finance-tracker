from fastapi import APIRouter, Depends, Query
from typing import Dict, List, Any
from sqlalchemy import extract
from datetime import datetime

from api.dependencies import get_current_user
from api.models import User, Transaction as DBTransaction
from api.db import SessionLocal
from src.models import TransactionData
from src.analytics import AnalyticsEngine
from src.storage import StorageManager

router = APIRouter(prefix="/api/stats", tags=["analytics"])
storage = StorageManager()

@router.get("/monthly")
async def get_monthly_stats(
    year: int = Query(..., description="Year"),
    month: int = Query(..., description="Month (1-12)"),
    current_user: User = Depends(get_current_user)
):
    with SessionLocal() as db:
        # Fetch transactions for the month
        txs_db = db.query(DBTransaction).filter(
            DBTransaction.user_id == current_user.id,
            extract('year', DBTransaction.timestamp) == year,
            extract('month', DBTransaction.timestamp) == month
        ).all()

        transactions = [
            TransactionData(
                id=t.id, type=t.type, amount=t.amount, description=t.description,
                bank=t.bank, category=t.category, account=t.account,
                timestamp=t.timestamp.isoformat(), raw_message=t.raw_message,
                status=t.status
            ) for t in txs_db
        ]

    engine = AnalyticsEngine(transactions)
    income_expense = engine.get_total_income_expense()
    cat_breakdown = engine.get_category_breakdown()

    return {
        "income": income_expense["income"],
        "expense": income_expense["expense"],
        "disbursed_expense": income_expense["disbursed_expense"],
        "breakdown": cat_breakdown
    }

@router.get("/daily")
async def get_daily_stats(
    year: int = Query(..., description="Year"),
    month: int = Query(..., description="Month (1-12)"),
    current_user: User = Depends(get_current_user)
):
    with SessionLocal() as db:
        txs_db = db.query(DBTransaction).filter(
            DBTransaction.user_id == current_user.id,
            extract('year', DBTransaction.timestamp) == year,
            extract('month', DBTransaction.timestamp) == month
        ).all()

        transactions = [
            TransactionData(
                id=t.id, type=t.type, amount=t.amount, description=t.description,
                bank=t.bank, category=t.category, account=t.account,
                timestamp=t.timestamp.isoformat(), raw_message=t.raw_message,
                status=t.status
            ) for t in txs_db
        ]

    engine = AnalyticsEngine(transactions)
    daily = engine.get_daily_breakdown()

    # Also get budget for daily context?
    # Spec says "Daily spending vs daily budget limit (if set)"
    config = storage.get_user_config(current_user)
    budgets = config.get("budgets", {})
    total_budget = budgets.get("Total", 0)

    # Calculate daily budget? usually (Total - Spent) / Days Remaining?
    # Or just return total budget and let frontend calc?
    # The endpoint output just says JSON.

    return {
        "daily_spending": daily,
        "monthly_budget": total_budget
    }

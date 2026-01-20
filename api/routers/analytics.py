from fastapi import APIRouter, Depends, Query, Body, HTTPException
from typing import Dict, List, Any, Optional
from sqlalchemy import extract, and_
from datetime import datetime, timedelta
import calendar

from api.dependencies import get_current_user, get_api_key
from api.models import User, Transaction as DBTransaction
from sqlalchemy.orm import Session
from api.db import get_db
from api.schemas import AnalyticsAnalyzeRequest
from src.models import TransactionData
from src.analytics import AnalyticsEngine
from src.storage import StorageManager
from src.llm_helper import analyze_spending_habits

router = APIRouter(prefix="/api/stats", tags=["analytics"])
storage = StorageManager()

def _get_engine_for_period(user_id: int, year: int, month: int, db) -> AnalyticsEngine:
    # Use date range for robustness
    start_date = datetime(year, month, 1)
    # Calculate end of month
    last_day = calendar.monthrange(year, month)[1]
    end_date = datetime(year, month, last_day, 23, 59, 59, 999999)

    txs_db = db.query(DBTransaction).filter(
        DBTransaction.user_id == user_id,
        DBTransaction.timestamp >= start_date,
        DBTransaction.timestamp <= end_date
    ).all()

    # Debug
    # print(f"DEBUG: Period {year}-{month}. User {user_id}. Found {len(txs_db)} txs. Start: {start_date}, End: {end_date}")

    transactions = [
        TransactionData(
            id=t.id, type=t.type, amount=t.amount, description=t.description,
            bank=t.bank, category=t.category, account=t.account,
            timestamp=t.timestamp.isoformat(), raw_message=t.raw_message,
            status=t.status
        ) for t in txs_db
    ]
    return AnalyticsEngine(transactions)

@router.get("/monthly")
async def get_monthly_stats(
    year: int = Query(..., description="Year"),
    month: int = Query(..., description="Month (1-12)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    engine = _get_engine_for_period(current_user.id, year, month, db)

    income_expense = engine.get_total_income_expense()
    cat_breakdown = engine.get_category_breakdown()
    account_breakdown = engine.get_account_breakdown()

    # Get budget info
    config = storage.get_user_config(current_user)
    budgets = config.get("budgets", {})

    return {
        "income": income_expense["income"],
        "expense": income_expense["expense"],
        "disbursed_expense": income_expense["disbursed_expense"],
        "breakdown": cat_breakdown,
        "account_breakdown": account_breakdown,
        "budgets": budgets
    }

@router.get("/daily")
async def get_daily_stats(
    year: int = Query(..., description="Year"),
    month: int = Query(..., description="Month (1-12)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    engine = _get_engine_for_period(current_user.id, year, month, db)

    daily = engine.get_daily_breakdown()

    config = storage.get_user_config(current_user)
    budgets = config.get("budgets", {})
    total_budget = budgets.get("Total", 0)

    return {
        "daily_spending": daily,
        "monthly_budget": total_budget
    }

@router.get("/trend")
async def get_trend_stats(
    months: int = Query(6, description="Number of months to look back"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns income/expense trend for the last N months (including current).
    """
    now = datetime.now()
    trend_data = []

    for i in range(months):
        # Calculate year/month walking backwards
        y = now.year
        m = now.month - i
        while m <= 0:
            m += 12
            y -= 1

        engine = _get_engine_for_period(current_user.id, y, m, db)
        totals = engine.get_total_income_expense()

        trend_data.append({
            "year": y,
            "month": m,
            "label": f"{calendar.month_name[m][:3]} {y}",
            "income": totals["income"],
            "expense": abs(totals["expense"]) # Return positive for chart
        })

    # Reverse to show chronological
    trend_data.reverse()
    return trend_data

@router.post("/analyze")
async def analyze_spending(
    request: AnalyticsAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    api_key: Optional[str] = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """
    Uses LLM to analyze spending habits.
    """
    # Determine context period
    now = datetime.now()
    year = request.year or now.year
    month = request.month or now.month

    engine = _get_engine_for_period(current_user.id, year, month, db)

    stats = {
        "income": engine.get_total_income_expense()["income"],
        "expense": engine.get_total_income_expense()["expense"],
        "breakdown": engine.get_category_breakdown()
    }

    context = {"stats": stats}

    analysis = analyze_spending_habits(request.prompt, context, api_key=api_key)
    return {"analysis": analysis}

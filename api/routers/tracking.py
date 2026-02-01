from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Optional
from datetime import datetime, timedelta, timezone, date
from calendar import monthrange
from sqlalchemy import or_, and_, func, case

from api.dependencies import get_current_user
from api.models import User, Transaction
from api.schemas import TrackingStatus, TrackingItem
from src.storage import StorageManager
from api.db import SessionLocal

router = APIRouter(prefix="/api/tracking", tags=["tracking"])
storage = StorageManager()

def get_date_range(period: str) -> tuple[datetime, datetime]:
    now = datetime.now()
    # Ensure consistent timezone if needed, but assuming naive/local for now based on context
    
    match period.lower():
        case "daily":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        case "weekly":
            # Assume Monday start
            start_date = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = (start_date + timedelta(days=6)).replace(hour=23, minute=59, second=59, microsecond=999999)
        case "monthly":
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # End of month
            _, last_day = monthrange(now.year, now.month)
            end_date = now.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)
        case "annually":
            start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = now.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
        case _:
            # Default to all time
            start_date = datetime.min.replace(tzinfo=timezone.utc)
            end_date = datetime.max.replace(tzinfo=timezone.utc)
        
    return start_date, end_date

@router.get("/status", response_model=List[TrackingStatus])
async def get_tracking_status(
    current_user: User = Depends(get_current_user)
):
    config = storage.get_user_config(current_user)
    tracking_items = config.get("tracking_items", [])
    
    if not tracking_items:
        return []

    results = []
    with SessionLocal() as db:
        for item in tracking_items:
            start_date, end_date = get_date_range(item.get("period", "monthly"))
            filters = item.get("filters", {})
            
            # Base query: User + Date Range
            base_filters = [
                Transaction.user_id == current_user.id,
                Transaction.timestamp >= start_date,
                Transaction.timestamp <= end_date
            ]
            
            # Filter Logic Construction
            criteria = []
            
            # 1. Categories
            filter_categories = filters.get("categories")
            if filter_categories:
                # Use ILIKE or func.lower for case insensitivity
                # SQLite supports LIKE but let's use lower() == lower() for portability
                criteria.append(func.lower(Transaction.category).in_([c.lower() for c in filter_categories]))

            # 2. Accounts
            filter_accounts = filters.get("accounts")
            if filter_accounts:
                for acc in filter_accounts:
                    sub_criteria = []
                    if acc.get("bank"):
                        sub_criteria.append(func.lower(Transaction.bank) == acc["bank"].lower())
                    if acc.get("account"):
                         sub_criteria.append(Transaction.account == acc["account"])
                    if acc.get("type"):
                        sub_criteria.append(func.lower(Transaction.type) == acc["type"].lower())
                    
                    if sub_criteria:
                        criteria.append(and_(*sub_criteria))
            
            # Combine Categories AND Accounts
            if not criteria:
                pass # if not extra criteria, we match all
            else:
                base_filters.append(and_(*criteria))

            # Aggregation Columns
            # Cost: Sum of abs(amount) where amount < 0
            # Note: SQLite stores float.
            spending_case = case(
                (Transaction.amount < 0, func.abs(Transaction.amount)),
                else_=0.0
            )

            # Net Disbursements: Sum of amount where amount > 0 AND category == "disbursement"
            # Only if flag is true
            disbursements_case = 0.0
            if item.get("net_disbursements"):
                disbursements_case = case(
                    (and_(Transaction.amount > 0, func.lower(Transaction.category) == "disbursement"), Transaction.amount),
                    else_=0.0
                )
            
            query = db.query(
                func.sum(spending_case).label("spending"),
                func.sum(disbursements_case).label("disbursements")
            ).filter(*base_filters)
            
            result = query.first()
            
            total_spending = (result.spending or 0.0) - (result.disbursements or 0.0)
            
            # Ensure non-negative?
            if total_spending < 0:
                total_spending = 0.0

            status_item = item.copy()
            status_item["current_amount"] = total_spending
            status_item["start_date"] = start_date.isoformat()
            status_item["end_date"] = end_date.isoformat()
            
            results.append(status_item)
            
    return results

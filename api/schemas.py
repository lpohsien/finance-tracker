from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class TransactionBase(BaseModel):
    bank_message: Optional[str] = None
    bank_name: Optional[str] = None
    timestamp: Optional[str] = None # ISO string
    remarks: Optional[str] = None

class TransactionParseRequest(TransactionBase):
    pass

class TransactionResponse(BaseModel):
    id: str
    amount: float
    description: str
    bank: str
    category: str
    timestamp: str # ISO
    type: str
    account: Optional[str] = None
    status: Optional[str] = None
    text_summary: Optional[str] = None # For Siri

class TransactionCreate(BaseModel):
    amount: float
    description: str
    bank: str
    category: Optional[str] = "Uncategorized"
    type: str
    timestamp: str # ISO
    account: Optional[str] = None

class TransactionUpdate(BaseModel):
    amount: Optional[float] = None
    description: Optional[str] = None
    category: Optional[str] = None
    type: Optional[str] = None
    timestamp: Optional[str] = None
    bank: Optional[str] = None
    status: Optional[str] = None

class BudgetSetRequest(BaseModel):
    category: str
    amount: float

class CategoryAction(BaseModel):
    categories: List[str]

class KeywordAction(BaseModel):
    category: str
    keywords: List[str]

class APIKeyUpdate(BaseModel):
    api_key: str

class AccountFilter(BaseModel):
    bank: Optional[str] = None
    account: Optional[str] = None
    type: Optional[str] = None

class TrackingFilters(BaseModel):
    categories: Optional[List[str]] = None
    accounts: Optional[List[AccountFilter]] = None

class TrackingItemBase(BaseModel):
    name: str
    type: str # "goal" or "limit"
    target_amount: float
    period: str # "daily", "weekly", "monthly", "annually"
    net_disbursements: bool = False
    filters: TrackingFilters

class TrackingItemCreate(TrackingItemBase):
    pass

class TrackingItem(TrackingItemBase):
    id: str

class TrackingStatus(TrackingItem):
    current_amount: float
    start_date: str # ISO
    end_date: str # ISO

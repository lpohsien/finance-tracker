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

class AnalyticsAnalyzeRequest(BaseModel):
    prompt: str
    year: Optional[int] = None
    month: Optional[int] = None

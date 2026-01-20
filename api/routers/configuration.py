from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Dict, Optional
from pydantic import BaseModel

from api.dependencies import get_current_user, get_api_key
from api.models import User
from api.db import SessionLocal
from src.storage import StorageManager
from src.security import encrypt_value

router = APIRouter(prefix="/api/config", tags=["configuration"])
storage = StorageManager()

class ConfigResponse(BaseModel):
    budgets: Dict[str, float]
    categories: List[str]
    keywords: Dict[str, List[str]]
    big_ticket_threshold: float
    api_key_set: bool

@router.get("", response_model=ConfigResponse)
async def get_config(
    current_user: User = Depends(get_current_user)
):
    config = storage.get_user_config(current_user)
    return {
        "budgets": config.get("budgets", {}),
        "categories": config.get("categories", []),
        "keywords": config.get("keywords", {}),
        "big_ticket_threshold": config.get("big_ticket_threshold", 0.0),
        "api_key_set": bool(current_user.google_api_key)
    }

@router.post("/budgets")
async def update_budget(
    category: str = Body(...),
    amount: float = Body(...),
    current_user: User = Depends(get_current_user)
):
    storage.update_user_budget(current_user, category, amount)
    return {"message": "Budget updated"}

@router.post("/categories")
async def add_categories(
    categories: List[str] = Body(..., embed=True),
    current_user: User = Depends(get_current_user)
):
    added, errors = storage.add_user_categories(current_user, categories)
    return {"added": added, "errors": errors}

@router.delete("/categories")
async def delete_categories(
    categories: List[str] = Body(..., embed=True),
    current_user: User = Depends(get_current_user)
):
    deleted, errors = storage.delete_user_categories(current_user, categories)
    return {"deleted": deleted, "errors": errors}

@router.post("/keywords")
async def add_keywords(
    category: str = Body(...),
    keywords: List[str] = Body(...),
    current_user: User = Depends(get_current_user)
):
    added, errors = storage.add_user_keywords(current_user, category, keywords)
    return {"added": added, "errors": errors}

@router.delete("/keywords")
async def delete_keywords(
    category: str = Body(...),
    keywords: List[str] = Body(...),
    current_user: User = Depends(get_current_user)
):
    deleted, errors = storage.delete_user_keywords(current_user, category, keywords)
    return {"deleted": deleted, "errors": errors}

@router.post("/apikey")
async def set_api_key(
    api_key: str = Body(..., embed=True),
    current_user: User = Depends(get_current_user)
):
    """
    Sets the Google API Key for the user (Encrypted).
    """
    encrypted = encrypt_value(api_key)

    with SessionLocal() as db:
        # Re-fetch user to attach to session
        user = db.merge(current_user)
        user.google_api_key = encrypted
        db.commit()

    return {"message": "API Key updated"}

@router.delete("/apikey")
async def delete_api_key(
    current_user: User = Depends(get_current_user)
):
    with SessionLocal() as db:
        user = db.merge(current_user)
        user.google_api_key = None
        db.commit()
    return {"message": "API Key removed"}

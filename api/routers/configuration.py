from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.responses import StreamingResponse
from typing import List, Dict, Optional
from pydantic import BaseModel
import uuid
import csv
import io
import json

from api.dependencies import get_current_user, get_api_key
from api.models import User
from api.db import SessionLocal
from api.schemas import TrackingItem, TrackingItemCreate
from src.storage import StorageManager
from src.security import encrypt_value
from src.config import TRANSACTION_TYPES

router = APIRouter(prefix="/api/config", tags=["configuration"])
storage = StorageManager()

class ConfigResponse(BaseModel):
    budgets: Dict[str, float]
    categories: List[str]
    keywords: Dict[str, List[str]]
    tracking_items: List[TrackingItem]
    big_ticket_threshold: float
    api_key_set: bool
    transaction_types: List[str]

@router.get("", response_model=ConfigResponse)
async def get_config(
    current_user: User = Depends(get_current_user)
):
    config = storage.get_user_config(current_user)
    return {
        "budgets": config.get("budgets", {}),
        "categories": sorted(config.get("categories", [])),
        "keywords": config.get("keywords", {}),
        "tracking_items": config.get("tracking_items", []),
        "big_ticket_threshold": config.get("big_ticket_threshold", 0.0),
        "transaction_types": TRANSACTION_TYPES,
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

@router.get("/export")
async def export_config(current_user: User = Depends(get_current_user)):
    """
    Exports user configuration as a JSON file.
    """
    config = storage.get_user_config(current_user)
    
    json_content = json.dumps(config, indent=2)
    
    return StreamingResponse(
        io.BytesIO(json_content.encode('utf-8')),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=config_export.json"}
    )


@router.delete("/apikey")
async def delete_api_key(
    current_user: User = Depends(get_current_user)
):
    with SessionLocal() as db:
        user = db.merge(current_user)
        user.google_api_key = None
        db.commit()
    return {"message": "API Key removed"}

@router.post("/tracking", response_model=TrackingItem)
async def add_tracking_item(
    item: TrackingItemCreate,
    current_user: User = Depends(get_current_user)
):
    config = storage.get_user_config(current_user)
    items = config.get("tracking_items", [])
    
    new_item = item.model_dump()
    new_item["id"] = str(uuid.uuid4())
    items.append(new_item)
    
    config["tracking_items"] = items
    storage.save_user_config(current_user, config)
    return new_item

@router.put("/tracking/{item_id}", response_model=TrackingItem)
async def update_tracking_item(
    item_id: str,
    item: TrackingItemCreate,
    current_user: User = Depends(get_current_user)
):
    config = storage.get_user_config(current_user)
    items = config.get("tracking_items", [])
    
    found = False
    updated_items = []
    updated_item_data = {}
    
    for existing in items:
        if existing["id"] == item_id:
            updated_item_data = item.model_dump()
            updated_item_data["id"] = item_id
            updated_items.append(updated_item_data)
            found = True
        else:
            updated_items.append(existing)
            
    if not found:
        raise HTTPException(status_code=404, detail="Tracking item not found")
        
    config["tracking_items"] = updated_items
    storage.save_user_config(current_user, config)
    return updated_item_data

@router.delete("/tracking/{item_id}")
async def delete_tracking_item(
    item_id: str,
    current_user: User = Depends(get_current_user)
):
    config = storage.get_user_config(current_user)
    items = config.get("tracking_items", [])
    
    filtered = [i for i in items if i["id"] != item_id]
    
    if len(filtered) == len(items):
        raise HTTPException(status_code=404, detail="Tracking item not found")
        
    config["tracking_items"] = filtered
    storage.save_user_config(current_user, config)
    return {"message": "Deleted"}

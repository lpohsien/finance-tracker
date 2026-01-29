from fastapi import APIRouter, Depends, HTTPException, Query, status, Request, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
from typing import List, Optional, Dict, Any
import uuid
import csv
import io
from datetime import datetime
from dateutil import parser as date_parser

from api.dependencies import get_current_user, get_api_key
from api.models import User
from api.db import SessionLocal
from api.schemas import (
    TransactionParseRequest, TransactionResponse, TransactionCreate,
    TransactionUpdate
)
from src.parser import TransactionParser
from src.storage import StorageManager, FIELDNAMES
from src.models import TransactionData
from src.config import TRANSACTION_TYPES
from api.models import Transaction as DBTransaction
from sqlalchemy import extract, or_, and_, text

router = APIRouter(prefix="/api/transactions", tags=["transactions"])
parser = TransactionParser()
storage = StorageManager()

def apply_filters(
    query,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    categories: Optional[List[str]] = None,
    accounts: Optional[List[str]] = None,
    types: Optional[List[str]] = None,
    banks: Optional[List[str]] = None,
    search: Optional[str] = None,
    match_case: bool = False,
    use_regex: bool = False
):
    # Time Filters
    if start_date:
        try:
            sd = date_parser.parse(start_date)
            query = query.filter(DBTransaction.timestamp >= sd)
        except:
            pass
    if end_date:
        try:
            ed = date_parser.parse(end_date)
            query = query.filter(DBTransaction.timestamp <= ed)
        except:
            pass
            
    if year:
        query = query.filter(extract('year', DBTransaction.timestamp) == year)
        if month:
            query = query.filter(extract('month', DBTransaction.timestamp) == month)
            
    # List Filters
    if categories:
        query = query.filter(DBTransaction.category.in_(categories))
    if accounts:
        query = query.filter(DBTransaction.account.in_(accounts))
    if types:
        query = query.filter(DBTransaction.type.in_(types))
    if banks:
        query = query.filter(DBTransaction.bank.in_(banks))

    # Search Filter
    if search:
        if use_regex:
            # Requires REGEXP support in SQL backend (added in api/db.py for sqlite)
            query = query.filter(DBTransaction.description.op("REGEXP")(search))
        else:
            if match_case:
                # SQLite is case-insensitive by default in some setups, but GLOB is case sensitive
                # Or usage of BINARY if possible. 
                # Ideally, simple LIKE is case-insensitive.
                # For case-sensitive, we can cast to binary or use custom logic.
                # Given SQLite limit, maybe just use standard LIKE and filter in python if strictly needed?
                # But 'glob' is case sensitive in SQLite.
                query = query.filter(DBTransaction.description.op("GLOB")(f"*{search}*"))
            else:
                query = query.filter(DBTransaction.description.ilike(f"%{search}%"))
                
    return query

@router.post("/parse", response_model=TransactionResponse)
async def parse_transaction(
    request: Request,
    parse_request: TransactionParseRequest,
    current_user: User = Depends(get_current_user),
    api_key: Optional[str] = Depends(get_api_key)
):
    """
    Parses a transaction from structured input (e.g. from Apple Shortcuts).
    Uses the user's configured categories and keywords.
    """
    config = storage.get_user_config(current_user)
    categories = config.get("categories")
    keywords = config.get("keywords")

    data = parse_request.model_dump()

    # Parse
    transaction_data, status_msg = parser.parse_structured_data(
        data,
        categories_list=categories,
        keywords_map=keywords,
        api_key=api_key
    )

    if not transaction_data:
        raise HTTPException(status_code=400, detail=status_msg or "Failed to parse transaction")

    # Ensure ID
    if not transaction_data.id:
        transaction_data.id = str(uuid.uuid4())

    storage.save_transaction(transaction_data, current_user)
    
    # Construct full path assuming default vite port 5173
    hostname = request.url.hostname or "localhost"
    port = request.url.port or 8000
    scheme = request.url.scheme or "http"
    full_path = f"{scheme}://{hostname}:{port}/transactions/{transaction_data.id}"

    # Prepare response
    resp = TransactionResponse(
        id=transaction_data.id,
        amount=transaction_data.amount,
        description=transaction_data.description,
        bank=transaction_data.bank,
        category=transaction_data.category or "Uncategorized",
        timestamp=transaction_data.timestamp,
        type=transaction_data.type or "Unknown",
        account=transaction_data.account,
        status=transaction_data.status,
        text_summary=f"Added SGD {transaction_data.amount:.2f} at {transaction_data.description}.",
        transaction_path=full_path
    )
    return resp

@router.post("", response_model=TransactionResponse)
async def add_transaction(
    request: TransactionCreate,
    current_user: User = Depends(get_current_user)
):
    tx_id = str(uuid.uuid4())
    tx_data = TransactionData(
        id=tx_id,
        type=request.type,
        amount=request.amount,
        description=request.description,
        bank=request.bank,
        category=request.category,
        account=request.account,
        timestamp=request.timestamp,
        status="Manual Entry"
    )
    storage.save_transaction(tx_data, current_user)

    return TransactionResponse(
        id=tx_id,
        amount=tx_data.amount,
        description=tx_data.description,
        bank=tx_data.bank,
        category=tx_data.category,
        timestamp=tx_data.timestamp,
        type=tx_data.type,
        account=tx_data.account,
        status=tx_data.status,
        text_summary="Transaction added."
    )

@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: str,
    update_data: TransactionUpdate,
    current_user: User = Depends(get_current_user)
):
    tx = storage.get_transaction(transaction_id, current_user)
    if not tx:
         raise HTTPException(status_code=404, detail="Transaction not found")

    config = storage.get_user_config(current_user)
    categories = config.get("categories", [])
    
    if update_data.category and update_data.category not in categories:
         raise HTTPException(status_code=400, detail=f"Invalid category. Allowed: {categories}")

    if update_data.type and update_data.type not in TRANSACTION_TYPES:
         raise HTTPException(status_code=400, detail=f"Invalid transaction type. Allowed: {TRANSACTION_TYPES}")

    if update_data.amount is not None:
        tx.amount = update_data.amount
    if update_data.description is not None:
        tx.description = update_data.description
    if update_data.category is not None:
        tx.category = update_data.category
    if update_data.type is not None:
        tx.type = update_data.type
    if update_data.timestamp is not None:
        tx.timestamp = update_data.timestamp
    if update_data.bank is not None:
        tx.bank = update_data.bank
    if update_data.status is not None:
        tx.status = update_data.status
        
    storage.save_transaction(tx, current_user)
    
    return TransactionResponse(
        id=tx.id,
        amount=tx.amount,
        description=tx.description,
        bank=tx.bank,
        category=tx.category,
        timestamp=tx.timestamp,
        type=tx.type,
        account=tx.account,
        status=tx.status,
        text_summary="Transaction updated."
    )

@router.get("/export")
async def export_transactions(
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    categories: Optional[List[str]] = Query(None, alias="category"),
    accounts: Optional[List[str]] = Query(None, alias="account"),
    types: Optional[List[str]] = Query(None, alias="type"),
    banks: Optional[List[str]] = Query(None, alias="bank"),
    search: Optional[str] = Query(None),
    match_case: bool = False,
    use_regex: bool = False,
    current_user: User = Depends(get_current_user)
):
    with SessionLocal() as db:
        query = db.query(DBTransaction).filter(DBTransaction.user_id == current_user.id)
        
        has_filter = any([
            year, month, start_date, end_date, 
            categories, accounts, types, banks, search
        ])
        
        # Consistent with View: if no filter, default to current month?
        # Specification says "export transactions in the transactions view". 
        # View defaults to current month. So yes.
        if not has_filter:
            current_date = datetime.now()
            query = query.filter(extract('year', DBTransaction.timestamp) == current_date.year)
            query = query.filter(extract('month', DBTransaction.timestamp) == current_date.month)
        else:
             query = apply_filters(
                query, start_date, end_date, year, month, 
                categories, accounts, types, banks, 
                search, match_case, use_regex
            )
            
        query = query.order_by(DBTransaction.timestamp.desc())
        txs = query.all()

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=FIELDNAMES)
        writer.writeheader()
        
        for t in txs:
            # Match schema with CSV fields
            row = {
                "id": t.id,
                "timestamp": t.timestamp.isoformat(),
                "bank": t.bank,
                "type": t.type,
                "amount": t.amount,
                "description": t.description,
                "account": t.account,
                "category": t.category,
                "raw_message": t.raw_message,
                "status": t.status
            }
            writer.writerow(row)

        output.seek(0)
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8')),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=transactions_export.csv"}
        )

@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_user)
):
    tx = storage.get_transaction(transaction_id, current_user.telegram_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
        
    return TransactionResponse(
        id=tx.id,
        amount=tx.amount,
        description=tx.description,
        bank=tx.bank,
        category=tx.category,
        timestamp=tx.timestamp,
        type=tx.type,
        account=tx.account,
        status=tx.status,
        text_summary=f"{tx.type} transaction of {tx.amount} at {tx.description}"
    )

@router.get("", response_model=List[TransactionResponse])
async def list_transactions(
    request: Request,
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    limit: int = 100,
    offset: int = 0,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    categories: Optional[List[str]] = Query(None, alias="category"),
    accounts: Optional[List[str]] = Query(None, alias="account"),
    types: Optional[List[str]] = Query(None, alias="type"),
    banks: Optional[List[str]] = Query(None, alias="bank"),
    search: Optional[str] = Query(None),
    match_case: bool = False,
    use_regex: bool = False,
    current_user: User = Depends(get_current_user)
):
    # Default to current month if no filtering provided at all
    has_filter = any([
        year, month, start_date, end_date, 
        categories, accounts, types, banks, search
    ])
    
    with SessionLocal() as db:
        query = db.query(DBTransaction).filter(DBTransaction.user_id == current_user.id)
        
        if not has_filter:
            current_date = datetime.now()
            query = query.filter(extract('year', DBTransaction.timestamp) == current_date.year)
            query = query.filter(extract('month', DBTransaction.timestamp) == current_date.month)
        else:
            query = apply_filters(
                query, start_date, end_date, year, month, 
                categories, accounts, types, banks, 
                search, match_case, use_regex
            )

        query = query.order_by(DBTransaction.timestamp.desc())
        query = query.offset(offset).limit(limit)

        txs = query.all()

        return [
            TransactionResponse(
                id=t.id,
                amount=t.amount,
                description=t.description,
                bank=t.bank,
                category=t.category,
                timestamp=t.timestamp.isoformat(),
                type=t.type,
                account=t.account,
                status=t.status
            ) for t in txs
        ]

@router.delete("/{transaction_id}")
async def delete_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_user)
):
    success = storage.delete_transaction(transaction_id, current_user)
    if not success:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"message": "Transaction deleted"}

@router.delete("")
async def clear_transactions(current_user: User = Depends(get_current_user)):
    # Note: storage.delete_all_transactions might need update if it doesn't use SQL
    # But storage implementation uses _get_db() usually.
    success = storage.delete_all_transactions(current_user)
    return {"message": "All transactions cleared"}

@router.post("/import", status_code=200)
async def import_transactions(
    file: UploadFile = File(...),
    create_new_categories: bool = Query(False),
    current_user: User = Depends(get_current_user)
):
    encoding = 'utf-8'
    content = await file.read()
    
    # Attempt to decode
    try:
        text_content = content.decode(encoding)
    except UnicodeDecodeError:
        encoding = 'latin-1' # Fallback
        text_content = content.decode(encoding)
        
    reader = csv.DictReader(io.StringIO(text_content))
    
    # Validate Headers
    if not reader.fieldnames:
         raise HTTPException(status_code=400, detail="Empty CSV")
         
    missing_cols = [col for col in FIELDNAMES if col not in reader.fieldnames]
    extra_cols = [col for col in reader.fieldnames if col not in FIELDNAMES]
    
    if missing_cols:
        # Prompt user to rectify
        return JSONResponse(status_code=400, content={
            "error": "structure_error",
            "detail": f"Missing columns: {', '.join(missing_cols)}. Expected: {', '.join(FIELDNAMES)}",
            "missing": missing_cols,
            "extra": extra_cols
        })
        
    # Get user config for validation
    config = storage.get_user_config(current_user)
    user_categories = set(c.lower() for c in config.get("categories", []))
    
    imported_count = 0
    errors = []
    new_categories_detected = set()
    
    valid_rows = []
    
    # Process Rows
    for row in reader:
        row_status = "OK"
        row_error = None
        
        # 1. UUID
        tx_id = row.get("id", "").strip()
        if not tx_id:
            tx_id = str(uuid.uuid4())
        
        # 2. Category
        cat = row.get("category", "")
        if not cat:
            cat = "Uncategorized"
        
        cat_lower = cat.lower()
        if cat_lower not in user_categories and cat_lower != "uncategorized":
            if create_new_categories:
                # Will be added later
                new_categories_detected.add(cat) # Preserve case from CSV? Or use lower?
                # Use the capitalized version from CSV if available, or just cat
                # But we normalized logic to lower check.
                pass
            else:
                row_error = f"Category '{cat}' not found"
        
        # 3. Timestamp
        ts_val = None
        ts_str = row.get("timestamp", "")
        try:
            ts_val = date_parser.parse(ts_str)
        except:
            row_error = f"Invalid timestamp: {ts_str}"
            
        # 4. Amount
        amt_val = 0.0
        try:
            amt_val = float(row.get("amount", 0))
        except:
            row_error = f"Invalid amount: {row.get('amount')}"
            
        if row_error:
            # Cache failure
            row["status"] = row_error
            errors.append(row)
        else:
            # Valid enough
            valid_rows.append({
                "id": tx_id,
                "timestamp": ts_val,
                "amount": amt_val,
                "description": row.get("description", ""),
                "bank": row.get("bank", ""),
                "type": row.get("type", ""),
                "account": row.get("account", ""),
                "category": cat, # Keep original case or lower? Spec says convert to lower.
                "raw_message": row.get("raw_message", ""),
                "status": row.get("status", "Imported")
            })

    # If we have new categories and create_new_categories is True, update config
    if create_new_categories and new_categories_detected:
        current_cats = config.get("categories", [])
        current_keywords = config.get("keywords", {})
        
        for new_cat in new_categories_detected:
            # Add to categories if not exists (case insensitive check done above)
            # Find if strictly in list
            if new_cat not in current_cats:
                 # Prefer Capitalized if possible? Let's just use what was in CSV
                 # Spec says: "convert all categories to lower case" in Validation section.
                 # So we save lowercase.
                 new_cat_lower = new_cat.lower()
                 if new_cat_lower not in [c.lower() for c in current_cats]:
                     current_cats.append(new_cat_lower)
                     # Add keyword
                     if new_cat_lower not in current_keywords:
                         current_keywords[new_cat_lower] = [new_cat_lower]
        
        config["categories"] = current_cats
        config["keywords"] = current_keywords
        storage.save_user_config(current_user, config)
        
        # Re-validate previously valid rows that might have had these categories? 
        # Logic above: if create_new_categories is True, we skipped the error. 
        # So valid_rows contains them.
        
    # Commit valid rows
    if valid_rows:
        # Check for duplicates? Row ID check.
        # Ideally bulk insert.
         with SessionLocal() as db:
            for vr in valid_rows:
                # Check DB
                existing = db.query(DBTransaction).filter(DBTransaction.id == vr["id"]).first()
                if existing:
                    # Skip or Update? Spec says "if uuid... is present... allow transaction to be imported". 
                    # Usually means overwrite or skip? 
                    # If ID exists, it's a duplicate. Safe to skip or treat as error?
                    # Migration logic skipped.
                    # Let's Skip but log? Or maybe Update? 
                    # Let's skip to be safe.
                    continue
                
                # Create
                # Ensure category is stored as lowercase per spec
                new_tx = DBTransaction(
                    id=vr["id"],
                    user_id=current_user.id,
                    timestamp=vr["timestamp"],
                    bank=vr["bank"],
                    type=vr["type"],
                    amount=vr["amount"],
                    description=vr["description"],
                    category=vr["category"].lower(),
                    account=vr["account"],
                    raw_message=vr["raw_message"],
                    status=vr["status"]
                )
                db.add(new_tx)
                imported_count += 1
            db.commit()

    return {
        "success": True,
        "imported_count": imported_count,
        "failed_count": len(errors),
        "errors": errors,  # Frontend generates CSV from this
        "new_categories_detected": list(new_categories_detected)
    }

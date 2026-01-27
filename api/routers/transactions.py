from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
import uuid
from datetime import datetime

from api.dependencies import get_current_user, get_api_key
from api.models import User
from api.schemas import (
    TransactionParseRequest, TransactionResponse, TransactionCreate,
    TransactionUpdate
)
from src.parser import TransactionParser
from src.storage import StorageManager
from src.models import TransactionData
from src.security import decrypt_value

router = APIRouter(prefix="/api/transactions", tags=["transactions"])
parser = TransactionParser()
storage = StorageManager()

@router.post("/parse", response_model=TransactionResponse)
async def parse_transaction(
    request: TransactionParseRequest,
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

    data = request.model_dump()

    # Parse
    transaction_data, status_msg = parser.parse_structured_data(
        data,
        categories_list=categories,
        keywords_map=keywords,
        api_key=api_key
    )

    if not transaction_data:
        raise HTTPException(status_code=400, detail=status_msg or "Failed to parse transaction")

    # Save automatically? Spec says: "Output: Returns parsed transaction details...".
    # Spec also says "Parse & Add Transaction". So yes, save.

    # Ensure ID
    if not transaction_data.id:
        transaction_data.id = str(uuid.uuid4())

    storage.save_transaction(transaction_data, current_user)

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
        text_summary=f"Added SGD {transaction_data.amount:.2f} at {transaction_data.description}."
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

@router.get("", response_model=List[TransactionResponse])
async def list_transactions(
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user)
):
    # StorageManager.get_transactions returns ALL. We need to filter.
    # Ideally StorageManager should support filtering to avoid loading all into memory.
    # But for migration compatibility, we load all and filter here, OR update StorageManager.
    # Given we are using SQL now, we SHOULD update StorageManager or just use DB directly here.
    # Using DB directly is cleaner for API.

    from api.models import Transaction as DBTransaction
    from api.db import SessionLocal

    with SessionLocal() as db:
        query = db.query(DBTransaction).filter(DBTransaction.user_id == current_user.id)

        if year:
            # SQLite specific or generic?
            # extract year from timestamp
            from sqlalchemy import extract
            query = query.filter(extract('year', DBTransaction.timestamp) == year)
            if month:
                query = query.filter(extract('month', DBTransaction.timestamp) == month)

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
    success = storage.delete_all_transactions(current_user)
    return {"message": "All transactions cleared"}

from fastapi.responses import StreamingResponse
import io
import csv
from src.storage import FIELDNAMES

@router.get("/export")
async def export_transactions(current_user: User = Depends(get_current_user)):
    txs = storage.get_transactions(current_user)

    # Generate CSV in memory
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=FIELDNAMES)
    writer.writeheader()
    for t in txs:
        writer.writerow(t.to_dict())

    output.seek(0)

    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=transactions.csv"}
    )

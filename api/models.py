from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    telegram_id = Column(Integer, unique=True, index=True, nullable=True)
    google_api_key = Column(String, nullable=True)  # Encrypted
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    configuration = relationship("UserConfiguration", back_populates="user", uselist=False, cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")

class UserConfiguration(Base):
    __tablename__ = "user_configurations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    # Storing config as JSON blobs for flexibility and compatibility with legacy format
    budgets = Column(JSON, default=dict)
    categories = Column(JSON, default=list)
    keywords = Column(JSON, default=dict)
    tracking_items = Column(JSON, default=list)
    big_ticket_threshold = Column(Float, default=0.0)

    user = relationship("User", back_populates="configuration")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, index=True) # UUID string
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    timestamp = Column(DateTime, index=True)
    bank = Column(String, index=True)
    type = Column(String)
    amount = Column(Float)
    description = Column(String)
    category = Column(String, index=True)
    account = Column(String)
    raw_message = Column(String, nullable=True)
    status = Column(String, nullable=True)

    user = relationship("User", back_populates="transactions")

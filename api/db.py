from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
import re
from sqlalchemy import event
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/finance.db")

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

@event.listens_for(engine, "connect")
def sqlite_engine_connect(dbapi_connection, connection_record):
    if not hasattr(dbapi_connection, "create_function"):
        return
    # Register REGEXP function for SQLite
    def regexp(expr, item):
        if not item:
            return False
        try:
            return re.search(expr, item, re.IGNORECASE) is not None
        except re.error:
            return False

    dbapi_connection.create_function("REGEXP", 2, regexp)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

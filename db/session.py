from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from helpers.config import load_config
from db.models import Base

def get_sqlite_engine():
    cfg = load_config()
    sqlite_path = cfg.chat_history["sqlite_path"]
    engine = create_engine(f"sqlite:///{sqlite_path}", future=True)
    Base.metadata.create_all(engine)
    return engine

SessionLocal = sessionmaker(bind=get_sqlite_engine(), autoflush=False, autocommit=False, future=True)

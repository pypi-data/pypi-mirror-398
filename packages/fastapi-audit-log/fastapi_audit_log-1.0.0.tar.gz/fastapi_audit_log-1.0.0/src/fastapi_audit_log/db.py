from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def create_session_factory(db_url: str):
    engine = create_engine(db_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False,autocommit=False)
    return engine, SessionLocal
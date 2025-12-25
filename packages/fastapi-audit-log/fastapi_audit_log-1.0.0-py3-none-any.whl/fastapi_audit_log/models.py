from sqlalchemy.orm import declarative_base
from sqlalchemy import Sequence,Column, Integer, String, DateTime, Float, Text
from datetime import datetime,timezone

Base = declarative_base()

def utcnow_naive():
    return datetime.now(timezone.utc).replace(tzinfo=None)

def get_audit_model(table_name: str):

    class AuditLog(Base):
        __tablename__ = table_name

        id = Column(Integer, Sequence('audit_log_seq'),primary_key=True)
        timestamp = Column(DateTime, default=utcnow_naive)
        method = Column(String(10))
        path = Column(String(255))
        status_code = Column(Integer)
        ip_address = Column(String(45))
        request_body = Column(Text, nullable=True)
        response_body = Column(Text, nullable=True)
        duration_ms = Column(Float)

    return AuditLog
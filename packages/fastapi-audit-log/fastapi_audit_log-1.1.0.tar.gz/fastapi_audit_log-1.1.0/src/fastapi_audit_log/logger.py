from fastapi import FastAPI
from .config import AuditConfig
from .db import create_session_factory
from .models import Base, get_audit_model
from .middleware import AuditMiddleware
from .cleanup import start_cleanup_loop
import asyncio

class AuditLogger:

    def __init__(self, app: FastAPI, **kwargs):

        self.config = AuditConfig(**kwargs)

        engine, SessionLocal = create_session_factory(self.config.db_url)
        AuditLog = get_audit_model(self.config.table_name)

        Base.metadata.create_all(bind=engine)

        app.add_middleware(
            AuditMiddleware,
            session_factory=SessionLocal,
            AuditLog=AuditLog,
            config=self.config
        )

        @app.on_event("startup")
        async def start_cleanup():
            asyncio.create_task(
                start_cleanup_loop(
                    SessionLocal,
                    AuditLog,
                    self.config.retention_days
                )
            )

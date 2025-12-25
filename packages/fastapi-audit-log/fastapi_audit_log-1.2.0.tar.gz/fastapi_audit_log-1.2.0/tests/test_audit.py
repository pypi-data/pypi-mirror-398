import pytest
from fastapi import FastAPI
from fastapi_audit_log import AuditLogger

def test_audit_logger_init():
    app = FastAPI()
    AuditLogger(app=app, db_url="sqlite:///./test.db")
    assert True
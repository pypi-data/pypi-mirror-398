from pydantic import BaseModel
from typing import Callable, List, Optional

class AuditConfig(BaseModel):
    db_url: str
    table_name: str = "fastapi_audit_logs"
    retention_days: int = 30

    exclude_paths: List[str] = []
    include_paths: List[str] = []
    methods: List[str] = ["POST", "PUT", "PATCH", "DELETE"]

    log_request_body: bool = False
    log_response_body: bool = False

    mask_fields: List[str] = ["password", "token"]

    user_id_getter: Optional[Callable] = None
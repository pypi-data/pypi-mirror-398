import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from starlette.responses import Response
from fastapi import BackgroundTasks

logger = logging.getLogger("fastapi-audit-log") 

def write_audit_log(session_factory, AuditLog, data: dict):
    db = session_factory()
    try:
        db.add(AuditLog(**data))
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

class AuditMiddleware(BaseHTTPMiddleware):

    def __init__(self, app, session_factory, AuditLog, config):
        super().__init__(app)
        self.session_factory = session_factory
        self.AuditLog = AuditLog
        self.config = config
    
    async def get_request_body(self,request: Request) -> str | None:
        try:
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type or "application/x-www-form-urlencoded" in content_type:
                body = await request.body()
                request._body = body  # re-inject for downstream
                return body.decode("utf-8") if body else None
        
            if "multipart/form-data" in content_type:
                
                # Read raw body without consuming stream
                body = await request.body()
                # Re-inject for downstream
                request._body = body
            
                form = await request.form() 
                data = {} 
                for key, value in form.items(): 
                    if hasattr(value, "filename"):
                        data[key] = f"[file {value.filename}skipped]" 
                    else: data[key] = value 
                    
                return str(data)
            
            return "[unsupported content type]"
        
        except Exception:
            return None
    
    def is_path_excluded(self,path: str, exclude_paths: list[str]) -> bool:
        return any(path.startswith(p) for p in exclude_paths)
    
    def is_path_included(self,path: str, include_paths: list[str]) -> bool:
        if not include_paths:
            return True
        return any(path.startswith(p) for p in include_paths)

    async def dispatch(self, request: Request, call_next):
        
        start = time.time()
        if not self.is_path_excluded(request.url.path, self.config.include_paths):
            return await call_next(request)
        
        if self.is_path_excluded(request.url.path, self.config.exclude_paths):
            return await call_next(request)

        if request.method not in self.config.methods:
            return await call_next(request)
        
        # Request body
        request_body = await self.get_request_body(request)
        response = await call_next(request)
        
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk
        
        duration = (time.time() - start) * 1000

     
        background_tasks = BackgroundTasks()
        background_tasks.add_task(
                write_audit_log,
                self.session_factory,
                self.AuditLog,
                {
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "request_body": request_body,
                    "response_body": response_body.decode("utf-8", errors="ignore"),
                    "ip_address": request.client.host if request.client else None,
                    "duration_ms": duration,
                }
            )
        

        return Response(
            content=response_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
            background=background_tasks
        )

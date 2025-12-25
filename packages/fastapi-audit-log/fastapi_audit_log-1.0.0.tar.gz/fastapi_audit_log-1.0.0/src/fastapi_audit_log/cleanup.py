from datetime import datetime, timedelta,timezone
import asyncio

async def cleanup_old_logs(session_factory, AuditLog, retention_days: int):

    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)

    try:
        db = session_factory()
        db.query(AuditLog).filter(
            AuditLog.timestamp < cutoff
        ).delete()
        db.commit()
    except Exception:
        pass
    finally:
        db.close()


async def start_cleanup_loop(session_factory, AuditLog, retention_days: int):
    while True:
        await cleanup_old_logs(session_factory, AuditLog, retention_days)
        await asyncio.sleep(60 * 60 * 24)  # every 24 hours

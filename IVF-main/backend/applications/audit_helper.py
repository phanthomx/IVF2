# applications/audit_helper.py
from applications.database import db
from applications.models import AuditLog
from flask import request

def log_action(user_id, action, endpoint=None):
    """Call this anywhere — does NOT commit, let the caller commit."""
    try:
        audit = AuditLog(
            user_id=user_id,
            ip_address=request.remote_addr,
            endpoint=endpoint or request.path,
            action=action
        )
        db.session.add(audit)
    except Exception as e:
        print(f"[AuditLog Error]: {e}")
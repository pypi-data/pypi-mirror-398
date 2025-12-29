
from datetime import datetime, timezone

def utcnow():
    """So linters don't cry about datetime.utcnow"""
    return datetime.now(timezone.utc)

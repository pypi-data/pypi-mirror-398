__all__ = ['until']

from datetime import datetime, timezone

def until(time):
    now = datetime.now(timezone.utc)
    later = datetime.fromisoformat((now.isoformat()[:11] + time)).replace(tzinfo=timezone.utc)
    dt = (later - now).total_seconds()
    if dt < 0: dt += 86400
    return round(dt)

__all__ = ['between']

from datetime import datetime, timezone

def between(start, end):
    now = datetime.now(timezone.utc)
    ts = lambda t: datetime.fromisoformat(now.isoformat()[:11] + t).replace(tzinfo=timezone.utc)
    start = ts(start)
    end = ts(end)
    if start <= end:
        return start <= now < end
    else:
        return now >= start or now < end

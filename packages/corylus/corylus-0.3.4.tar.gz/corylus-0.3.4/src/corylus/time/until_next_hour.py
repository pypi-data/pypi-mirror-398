__all__ = ['until_next_hour']

from datetime import datetime, timedelta, timezone

def until_next_hour(delta=0, ms=False):
    now = datetime.now(timezone.utc)
    later = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    dt = (later - now).total_seconds() + delta
    if dt < 0: dt += 3600
    return int(dt * (1000 if ms else 1))

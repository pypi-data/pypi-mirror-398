__all__ = ['until_next_minutes']

from datetime import datetime, timedelta, timezone

def until_next_minutes(n, delta=None, ms=False):
    if delta is None: delta = n / 2
    now = datetime.now(timezone.utc)
    later = now + timedelta(minutes=n)
    later += timedelta(minutes=delta - (later.minute % n))
    dt = (later - now).total_seconds()
    return int(dt * (1000 if ms else 1))

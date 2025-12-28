__all__ = ['to_datetime']

from datetime import datetime, timezone
from .jd2epoch import *

def to_datetime(a):
    if isinstance(a, datetime): return a
    return datetime.fromtimestamp(jd2epoch(a), timezone.utc)

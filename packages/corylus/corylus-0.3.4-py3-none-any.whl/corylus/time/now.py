__all__ = ['now']

from datetime import datetime
from .from_datetime import *

def now(day=False):
    jd = from_datetime(datetime.now())
    return round(jd) if day else jd

__all__ = ['julian_day']

import pytz
from datetime import datetime, timedelta
from dateutil.parser import parse

from .from_datetime import *

def julian_day(a, utc=True):
    dt = datetime.now() - timedelta(days=-a) if isinstance(a, int) else parse(a)
    if utc and dt.utcoffset() is None:
        dt = pytz.utc.localize(dt)
    return int(from_datetime(dt) + 0.5)

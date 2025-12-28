__all__ = ['julian_date']

import pytz
from dateutil.parser import parse

from .from_datetime import *

def julian_date(a, utc=True):
    dt = parse(a)
    if utc and dt.utcoffset() is None:
        dt = pytz.utc.localize(dt)
    return from_datetime(dt)

__all__ = ['from_datetime']

from datetime import datetime

from .epoch2jd import *

def from_datetime(a):
    if isinstance(a, datetime):
        return epoch2jd(a.timestamp())

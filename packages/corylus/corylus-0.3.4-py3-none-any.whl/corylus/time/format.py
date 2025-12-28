__all__ = ['format']

from .to_datetime import *

def format(a):
    return to_datetime(a).isoformat(timespec='milliseconds').replace('+00:00', 'Z')

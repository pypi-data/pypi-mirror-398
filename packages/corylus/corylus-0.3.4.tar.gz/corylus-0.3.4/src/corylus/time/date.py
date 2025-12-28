__all__ = ['date']

from datetime import datetime
from dateutil.parser import parse

from .jd2epoch import *
from .now import *

def date(a=None, all=False, format=None):
    if a is None or a == 'today': a = now()
    if a == 'yesterday': a = now() - 1
    d = datetime.fromtimestamp(jd2epoch(a)) if isinstance(a, (int, float)) else parse(a)
    if not format:
        format = '%Y-%m-%dT%H:%M:%S' if all else '%Y-%m-%d'
    elif format == 'nl':
        format = '%d-%m-%Y'
    return d.strftime(format)

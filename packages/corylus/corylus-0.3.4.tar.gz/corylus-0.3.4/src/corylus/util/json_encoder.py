__all__ = ['JSONEncoder']

from collections.abc import Iterator
from datetime import datetime, timezone, date, time
from decimal import Decimal
from types import SimpleNamespace
import json

class JSONEncoder(json.JSONEncoder):
    def default(self, a):
        if isinstance(a, Decimal):
            # https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GettingStarted.Python.03.html
            return float(a) if abs(a) % 1 > 0 else int(a)
        elif isinstance(a, datetime):
            return a.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
        elif isinstance(a, date):
            return str(a)
        elif isinstance(a, time):
            return str(a)
        elif isinstance(a, bytes):
            return a.decode()
        elif isinstance(a, SimpleNamespace):
            return vars(a)
        elif isinstance(a, memoryview):
            return a.hex()
        elif hasattr(a, 'lower') and hasattr(a, 'upper'):
            # NumericRange in postgresql
            return [a.lower, a.upper]
        elif isinstance(a, Iterator):
            return list(a)
        else:
            return super(JSONEncoder, self).default(a)

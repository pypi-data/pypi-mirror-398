__all__ = ['to_json']

import json
from .json_encoder import JSONEncoder

def to_json(a, pretty=False):
    return json.dumps(
        a,
        cls=JSONEncoder,
        separators=((', ', ': ') if pretty else (',', ':')),
        indent=('    ' if pretty else None)
    )

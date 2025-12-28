__all__ = ['load']

from pathlib import Path
import json
import yaml

def load(a, base='.'):
    if not isinstance(a, str): return a
    if a.startswith('{') or a.startswith('['): return json.loads(a)
    with open(Path(base, a).resolve()) as file:
        return json.load(file) if a.endswith('.json') else yaml.safe_load(file)


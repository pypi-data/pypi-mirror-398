# [code by GPT-4.1](urn:uuid:2a73019a-1285-811a-ba2a-f7079e4767e1)

__all__ = ['substitute']

import re

def substitute(s, data_a, data_b=None, *, raw=False):
    """
    Substitute embedded JSONPath-like expressions:
    - $.foo.bar uses data_a
    - $foo.bar uses data_b
    If s is not a string, return it unchanged.
    If raw is True and the substitution covers the entire string, return
    the resolved value as-is (no str conversion).
    """
    if not isinstance(s, str):
        return s

    pattern = re.compile(r'(\$\.[\w\-\.]+|\$[\w\-\.]+)')

    # If the whole string matches a single path, return raw if requested
    match = pattern.fullmatch(s.strip())
    if match:
        path = match.group(0)
        if path.startswith('$.'):
            value = resolve_path(data_a, path)
        else:
            value = resolve_path(data_b, path) if data_b is not None else None
        if raw:
            return value
        return str(value) if value is not None else ''
    
    # Otherwise, replace all occurrences with stringified values
    def replacer(match):
        path = match.group(0)
        if path.startswith('$.'):
            value = resolve_path(data_a, path)
        else:
            value = resolve_path(data_b, path) if data_b is not None else ''
        return str(value) if value is not None else ''

    return pattern.sub(replacer, s)

def resolve_path(data, path):
    """Resolve dot-separated paths in nested dict/list structures."""
    if path.startswith('$.'):
        path = path[2:]
    elif path.startswith('$'):
        path = path[1:]
    parts = path.split('.') if path else []
    current = data
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list):
            try:
                idx = int(part)
                current = current[idx]
            except (ValueError, IndexError):
                return None
        else:
            return None
        if current is None:
            return None
    return current

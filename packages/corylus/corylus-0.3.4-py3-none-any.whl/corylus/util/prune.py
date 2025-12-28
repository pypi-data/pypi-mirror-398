__all__ = ['prune']

def prune(a, empty_string=True, empty_list=False, recursive=False):
    if isinstance(a, list):
        if empty_list and len(a) == 0: return None
        return [prune(x, empty_string, empty_list) for x in a if x is not None and (x != '' or not empty_string)]
    if not isinstance(a, dict): return a
    result = {}
    for key, value in a.items():
        v = prune(value, empty_string, empty_list, recursive) if recursive else value
        if v is not None and (v != '' or not empty_string) and (not isinstance(v, list) or len(v) > 0 or not empty_list):
            result[key] = v
    return result

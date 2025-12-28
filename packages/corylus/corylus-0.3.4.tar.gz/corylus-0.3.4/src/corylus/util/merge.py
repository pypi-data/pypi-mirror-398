__all__ = ['merge']

def merge(a, b, overwrite=True):
    if a is None: a = {}
    if b:
        for key in b:
            ak = a.get(key)
            bk = b.get(key)
            if isinstance(ak, dict) and isinstance(bk, dict):
                merge(ak, bk, overwrite)
            elif overwrite or key not in a:
                a[key] = bk
    return a

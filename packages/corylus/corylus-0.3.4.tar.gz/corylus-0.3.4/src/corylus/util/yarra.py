__all__ = ['yarra']

def yarra(a, first=False):
    if isinstance(a, list):
        if len(a) == 0:
            return None
        elif len(a) == 1 or first:
            return a[0]
    return a

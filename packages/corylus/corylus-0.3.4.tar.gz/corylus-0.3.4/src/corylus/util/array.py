__all__ = ['array']

from .isiterator import *

def array(a):
    if isiterator(a):
        return list(a)
    elif isinstance(a, (list, tuple)):
        return a
    elif a is None:
        return []
    else:
        return [a]

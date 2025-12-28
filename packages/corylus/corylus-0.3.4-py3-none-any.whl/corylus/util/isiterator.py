__all__ = ['isiterator']

import collections
from io import BufferedReader

IGNORE = (str, bytes, list, dict, tuple, BufferedReader)

def isiterator(a):
    return not isinstance(a, IGNORE) and isinstance(a, collections.abc.Iterable)

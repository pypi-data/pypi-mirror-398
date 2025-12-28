__all__ = ['with_attrs']

# by DiogoNeves (https://stackoverflow.com/a/29286574)

from functools import wraps

def with_attrs(**func_attrs):
    """Set attributes in the decorated function, at definition time.
    Only accepts keyword arguments.
    E.g.:
        @with_attrs(counter=0, something='boing')
        def count_it():
            count_it.counter += 1
        print count_it.counter
        print count_it.something
        # Out:
        # >>> 0
        # >>> 'boing'
    """
    def attr_decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)

        for attr, value in func_attrs.items():
            setattr(wrapper, attr, value)

        return wrapper

    return attr_decorator

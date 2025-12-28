__all__ = ['home2tilde']

import os

def home2tilde(path):
    home = os.path.expanduser('~')
    abs_path = os.path.abspath(path)
    if abs_path.startswith(home):
        # Avoid cases like '/home/userX' being replaced inappropriately
        after_home = abs_path[len(home):]
        if after_home == '' or after_home[0] == os.sep:
            return '~' + after_home
    return abs_path


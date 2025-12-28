__all__ = ['jd2epoch']

def jd2epoch(a):
    return (a - 2440587.5) * 86400

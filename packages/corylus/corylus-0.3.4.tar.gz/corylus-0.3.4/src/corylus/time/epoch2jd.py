__all__ = ['epoch2jd']

def epoch2jd(a):
    return 2440587.5 + (a / 86400)

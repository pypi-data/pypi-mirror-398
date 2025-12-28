__all__ = ['local2utc']

def local2utc(dt, local=None):
    import pytz
    from datetime import datetime
    from dateutil.parser import parse
    if not local or isinstance(local, str):
        local = pytz.timezone(local or 'Europe/Amsterdam')
    if isinstance(dt, str): dt = parse(dt)
    local_dt = local.localize(dt)
    return local_dt.astimezone(pytz.utc)

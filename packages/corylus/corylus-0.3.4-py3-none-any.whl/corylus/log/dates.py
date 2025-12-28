from datetime import datetime, UTC


def unix_to_julian(unix_timestamp: float) -> float:
    """
    Convert Unix timestamp to Julian date.

    Returns:
        Julian date as a float (days since -4713-01-01 12:00:00 UTC)
    """
    dt = datetime.fromtimestamp(unix_timestamp, UTC)

    year = dt.year
    month = dt.month
    day = dt.day
    hour = dt.hour
    minute = dt.minute
    second = dt.second

    if month <= 2:
        year -= 1
        month += 12

    a = year // 100
    b = 2 - a + (a // 4)

    julian_date = (
        int(365.25 * (year + 4716))
        + int(30.6001 * (month + 1))
        + day
        + b
        - 1524.5
    )

    time_fraction = (hour + (minute + second / 60.0) / 60.0) / 24.0
    julian_date += time_fraction

    return julian_date

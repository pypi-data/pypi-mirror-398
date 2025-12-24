from datetime import datetime, timedelta


def utc2local(lon, utc_date, utc_time):
    """
    Convert UTC date and time to local date and time based on longitude.

    Args:
        lon (float): Longitude in degrees (-180 to 180)
        utc_date (str): UTC date in 'YYYYMMDD' format
        utc_time (str): UTC time in 'HH:MM' format

    Returns:
        tuple: (local_date, local_time) where:
            - local_date is in 'YYYYMMDD' format
            - local_time is in 'HH:MM' format
    """
    # Calculate timezone offset (1 hour per 15 degrees of longitude)
    timezone = round(lon / 15)

    # Parse input date and time (handle both YYYYMMDD and YYYY/MM/DD formats)
    if "/" in utc_date:
        # Handle YYYY/MM/DD format
        date_parts = utc_date.split("/")
        year = int(date_parts[0])
        month = int(date_parts[1])
        day = int(date_parts[2])
    else:
        # Handle YYYYMMDD format
        year = int(utc_date[:4])
        month = int(utc_date[4:6])
        day = int(utc_date[6:8])
    hour = int(utc_time.split(":")[0])
    minute = int(utc_time.split(":")[1])

    # Create datetime object
    dt = datetime(year, month, day, hour, minute)

    # Apply timezone offset
    dt_local = dt + timedelta(hours=timezone)

    # Format output
    local_date = dt_local.strftime("%Y%m%d")
    local_time = dt_local.strftime("%H:%M")

    return local_date, local_time

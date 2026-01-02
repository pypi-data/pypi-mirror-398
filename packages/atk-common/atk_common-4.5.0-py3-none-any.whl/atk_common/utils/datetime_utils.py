from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

def get_utc_date_time():
    return datetime.now(timezone.utc)

def get_utc_date_time_str():
    return str(datetime.now(timezone.utc))

def get_utc_date_time_str_with_z():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

def seconds_to_utc_timestamp(seconds):
    return str(datetime.fromtimestamp(seconds, tz=timezone.utc))

def get_utc_date_from_iso(date_time):
    dt = datetime.fromisoformat(date_time)
    dt_utc = dt.astimezone(timezone.utc)
    return str(dt_utc.date())

def get_utc_iso_date_time():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

def adjust_millisescond(dt_str):
    if '.' in dt_str:
        dt_part, frac = dt_str.split('.')
        frac = frac[:6]  # keep only the first 6 digits
        dt_str_clean = f"{dt_part}.{frac}"
        return dt_str_clean
    else:
        dt_str_clean = dt_str
        return dt_str_clean

# Original datetime string, handles:
# dt_str = '2023-02-01T14:13:08.653133+01:00'
# dt_str = '2023-02-01T14:13:08.653133 01:00'
# dt_str = '2024-01-03T08:13:52.705474147'
def convert_to_utc(dt_str):
    # Split datetime and offset
    if '+' in dt_str:
        parts = dt_str.split('+')
    else:
        parts = dt_str.split(' ')
    if len(parts) == 2:
        dt_part, offset_part = parts
    else:
        dt_part = parts[0]
        offset_part = None  # or set a default if needed

    dt_part = adjust_millisescond(dt_part)
    dt_naive  = datetime.fromisoformat(dt_part)

    if offset_part is None:
        dt_aware = dt_naive.replace(tzinfo=ZoneInfo("Europe/Berlin"))
        dt_utc = dt_aware.astimezone(ZoneInfo("UTC"))
        return dt_utc.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    else:
        # Create a timezone object using the offset
        hours_offset = int(offset_part.split(':')[0])
        minutes_offset = int(offset_part.split(':')[1])
        tzinfo = timezone(timedelta(hours=hours_offset, minutes=minutes_offset))

        # Assign the timezone to the datetime
        dt_with_tz = dt_naive.replace(tzinfo=tzinfo)

        # Convert to UTC
        dt_utc =dt_with_tz.astimezone(timezone.utc)
        return dt_utc.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

# Original datetime string, handles:
# dt_str = '2023-02-01 14:13:08.653133 +01:00'
def convert_to_utc_image_dt(dt_str):
    dt_str = dt_str.strip()
    # Detect offset
    if '+' in dt_str:
        parts = dt_str.split('+')
        sign = '+'
    elif '-' in dt_str[10:]:  # avoid confusion with date part
        parts = dt_str.split('-')
        sign = '-'
    else:
        parts = [dt_str]
        sign = None

    if len(parts) == 2:
        dt_part = parts[0].strip()
        offset_part = parts[1].strip()
        if sign == '-':
            offset_part = '-' + offset_part
        else:
            offset_part = '+' + offset_part
    else:
        dt_part = parts[0].strip()
        offset_part = None

    dt_part = adjust_millisescond(dt_part)
    dt_naive = datetime.fromisoformat(dt_part)

    if offset_part is None:
        dt_aware = dt_naive.replace(tzinfo=ZoneInfo("Europe/Berlin"))
        dt_utc = dt_aware.astimezone(ZoneInfo("UTC"))
    else:
        offset_hours, offset_minutes = map(int, offset_part.split(':'))
        delta = timedelta(hours=offset_hours, minutes=offset_minutes)
        tz = timezone(delta)
        dt_aware = dt_naive.replace(tzinfo=tz)
        dt_utc = dt_aware.astimezone(timezone.utc)

    return dt_utc.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
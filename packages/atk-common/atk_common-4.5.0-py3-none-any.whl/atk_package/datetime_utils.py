from datetime import datetime, timezone

def date_time_utc(column):
    return 'TO_CHAR({0} at time zone \'UTC\', \'yyyy-mm-dd hh24:mi:ss.ms"Z"\')'.format(column)

def get_utc_date_time():
    return str(datetime.now(timezone.utc))

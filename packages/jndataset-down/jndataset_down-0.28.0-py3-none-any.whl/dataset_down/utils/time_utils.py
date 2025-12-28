
from datetime import datetime
import pytz
default_timezone = 'Asia/Shanghai'
default_time_format = '%Y-%m-%d %H:%M:%S'


def get_current_formatted_time(timezone=default_timezone) -> str:
    formatted_date = get_current_time(timezone).strftime(default_time_format)
    return formatted_date

def get_current_time(timezone=default_timezone) -> datetime:
    now_utc = datetime.now(tz=pytz.utc)
    tz = pytz.timezone(timezone)
    return now_utc.astimezone(tz)

def get_datetime_from_formatted_str(time_str, timezone=default_timezone) -> datetime:
    if time_str is None or len(time_str) == 0:
        raise ValueError("time string can not be empty")
    timezone = pytz.timezone(timezone)
    return datetime.strptime(time_str, default_time_format).replace(tzinfo=timezone)




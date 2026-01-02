import datetime
import re

def dt_from_filepath(filepath: str, pattern=r"(\d{8}\.\d{4})") -> datetime.datetime:
    match = re.search(pattern, filepath)
    if not match:
        raise RuntimeError("Could not determine time from filepath")
    timestamp_str = match.group(1)
    dt = datetime.datetime.strptime(timestamp_str, "%Y%m%d.%H%M")
    dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt
"""
HOBO-time-util:
Helper functions to convert between datetime formats

See LICENSE and AUTHORS for more info
"""

from datetime import datetime, timezone
import logging

#
# Return a datetime object using the supported string format:
#   YYYY-MM-DD HH:MM:SS
# will throw Value error otherwise
#
def get_datetime(datestr):
    """ Converts datetime string into datetime object."""
    date_fmt = "%Y-%m-%d %H:%M:%S"
    # Remove suffix for UTC
    # No TZ support: UTC always assumed
    if datestr[-1] == "Z":
        datestr = datestr[:-1]
    try:
        date = datetime.strptime(datestr, date_fmt)
        return date
    except ValueError:
        logging.error(f"HOBO-log] get_datetime - couldn't process timestamp value: {datestr}")
        raise


def timestamp_to_datestr(timestamp):
    """Convert timestamp int to date string."""
    # Example output: 2021-05-20 17:50:00
    dt = datetime.utcfromtimestamp(timestamp)
    datestr = dt.isoformat(sep=" ", timespec="seconds")
    return datestr


def datetime_to_datestr(dt):
    """Convert datetime to string."""
    datestr = dt.isoformat(sep=" ", timespec="seconds")
    return datestr


#
# Convert datetime string to timestamp int
#
def datestr_to_timestamp(datestr):
    """Converts datetime string into timestamp."""
    date_fmt = "%Y-%m-%d %H:%M:%S"
    # Remove suffix for UTC
    # No TZ support: UTC always assumed
    if datestr[-1] == "Z":
        datestr = datestr[:-1]
    try:
        date = datetime.strptime(datestr, date_fmt)
    except ValueError:
        logging.error(f"[HOBO-log] Error - couldn't process timestamp value: {datestr}")
        date = datetime.utcnow()
    timestamp = int(date.replace(tzinfo=timezone.utc).timestamp()) # Truncating to int
    return timestamp

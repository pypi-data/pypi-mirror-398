"""
HOBO-link:
API requests and auth functions

See LICENSE and AUTHORS for more info
"""

import requests
import logging
import time
from . import hobo_config_import as config

from datetime import datetime, timedelta
from urllib3.exceptions import ReadTimeoutError
from requests.exceptions import ConnectionError, ReadTimeout, HTTPError
from .hobo_time_util import datetime_to_datestr

#
# HOBOLink: Request for sensor data
#
def api_query(logger, start_date_time=None, end_date_time=None):
    """Makes an API request for data on individual loggers."""
    if start_date_time is None:
        raise ValueError("[HOBO-log] Start datetime not set")
    if not isinstance(start_date_time, datetime):
        raise TypeError("[HOBO-log] Expected start_date_time to be a datetime object")

    cfg = config.get_config()

    min_api_time_delta = cfg["min_api_time_delta_minutes"]

    start_date_time_str = datetime_to_datestr(start_date_time)
    if end_date_time is None:
        raise ValueError("[HOBO-log] End_date_time not set")
    if not isinstance(end_date_time, datetime):
        raise TypeError("[HOBO-log] Expected end_date_time to be a datetime object")
    if end_date_time <= start_date_time:
        # HOBO API seems to hang if the end date less or equal to the
        # start date. Raise an exception here to avoid that
        raise ValueError("[HOBO-log] end_date_time >= start_date_time")
    if end_date_time - start_date_time < timedelta(minutes=min_api_time_delta):
        # Make sure we are getting at least min_api_time_delta minutes of data
        end_date_time = start_date_time + timedelta(minutes=min_api_time_delta)

    end_date_param_str = datetime_to_datestr(end_date_time)

    #
    # Construct request to submit
    #
    req = f"{cfg['query_endpoint']}?"
    req += f"loggers={logger}&"
    req += f"start_date_time={start_date_time_str}&"
    req += f"end_date_time={end_date_param_str}"
    logging.debug(f"[HOBO-log] Sending request to HOBOLink: [{req}]")

    cfg = config.get_config()
    req_timeout_conn = cfg["request_timeout_connection"]
    req_timeout_read = cfg["request_timeout_read"]
    kwargs = {"timeout": (req_timeout_conn, req_timeout_read)}
    retry_times = (0.1, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 60.0)
    retry = 0
    
    token = cfg["token"]
    api_call_header = {
        "accept": "application/json",
        "Authorization": "Bearer " + token
    } 

    while True:
        try:
            r = requests.get(req, headers=api_call_header, verify=True, **kwargs)
            r.raise_for_status()
            r_json = r.json()
            r_msg = r_json["message"]
            logging.debug(f"[HOBO-log] Query {r_msg}")
            time.sleep(5)
            return r_json
        except ConnectionError as req_exception:
            logging.error(f"[HOBO-log] API connection error: {req_exception}")
            logging.debug("[HOBO-log] Retrying request after connection error")
        except ReadTimeoutError as timeout_error_msg:
            logging.error(f"[HOBO-log] Urllib read timeout: {timeout_error_msg}")
            logging.debug("[HOBO-log] Retrying request after urllib time out")
        except ReadTimeout as requests_timeout_msg:
            logging.error(f"[HOBO-log] API request read timeout: {requests_timeout_msg}")
            logging.debug("[HOBO-log] Retrying request after request timeout")
        except HTTPError as http_error_msg:
            logging.error(f"[HOBO-log] API request HTTP error: {http_error_msg}")
            logging.debug("[HOBO-log] Retrying request after HTTP error")
        if retry >= len(retry_times):
            sleep_time = retry_times[-1]
        else:
            sleep_time = retry_times[retry]
        logging.debug(f"[HOBO-log] Sleeping for: {sleep_time}")
        time.sleep(sleep_time)
        retry += 1
        logging.debug(f"[HOBO-log] Retry: {retry}")

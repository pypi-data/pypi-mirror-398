# -*- coding: utf-8 -*-
import datetime
import time
from datetime import datetime as dt

import pytz


def current_date(days=0):
    """
    Get the current date in format: YYYY-MM-DD

    :param days: 0 represents today, positive number for previous days, negative for future days.
    :return: date object
    """
    return datetime.date.today() - datetime.timedelta(days=days)


def current_time():
    """
    Get the current time in format: HH:MM:SS

    :return: str
    """
    return (datetime.datetime.now() + datetime.timedelta(days=0)).strftime('%H:%M:%S')


def date_format(area, source_date):
    """
    Convert to standard date format: YYYY-MM-DD

    :param area: timezone name
    :param source_date: date string with GMT info
    :return: str or original input if parsing fails
    """
    if isinstance(source_date, datetime.date):
        return source_date.strftime('%Y-%m-%d')
    try:
        date_str = source_date.split('GMT')[0].strip()
        dt_ = dt.strptime(date_str, '%a %b %d %Y %H:%M:%S')
        tz = pytz.timezone(area)
        dt_with_tz = tz.localize(dt_)
        return dt_with_tz.strftime('%Y-%m-%d')
    except Exception:
        return source_date


def datetime_exchange(source_date):
    """
    Convert datetime object to string format: YYYY-MM-DD HH:MM:SS

    :param source_date: datetime object or None
    :return: formatted datetime string or 0 if it's a specific default value
    """
    if source_date is None:
        return source_date
    elif source_date == datetime.datetime(1970, 1, 1, 8, 0):
        return 0
    else:
        return source_date.strftime('%Y-%m-%d %H:%M:%S')


def date_to_timestamp(date_str: str, time_zone):
    """
    Convert a date string to timestamp of midnight in specified timezone

    :param date_str: date string in format 'YYYY-MM-DD'
    :param time_zone: target timezone name
    :return: tuple of localized datetime and its timestamp
    """
    try:
        datetime_obj = dt.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        datetime_obj = dt.strptime(date_str.strftime("%Y-%m-%d"), '%Y-%m-%d')

    naive_datetime = dt.strptime(datetime_obj.strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
    utc_datetime = pytz.utc.localize(naive_datetime)
    
    if time_zone is None:
        # 使用 UTC 作为默认 fallback
        country_timezone = pytz.utc
    else:
        country_timezone = pytz.timezone(time_zone)
    country_datetime = utc_datetime.astimezone(country_timezone)

    return country_datetime, int(country_datetime.timestamp())


def generate_hour_list(max_hour=24):
    """
    Generate a list of hours from 1 to max_hour

    :param max_hour: maximum hour value
    :return: list of dictionaries with 'label' and 'key'
    """
    return [{'label': f'{i} hour', 'key': i} for i in range(1, max_hour + 1)]

def generate_limit_list(max=100):
    return [{'label': f'{i}', 'key': i} for i in range(10, max + 10, 10)]

def datetime_format(day_=0):
    """
    Format current datetime to string without separators

    :param day_: days offset
    :return: formatted datetime string as 'YYYYMMDDHHMMSS'
    """
    now_ = datetime.datetime.now()
    delta = datetime.timedelta(days=int(day_))
    return (now_ + delta).strftime('%Y%m%d%H%M%S')

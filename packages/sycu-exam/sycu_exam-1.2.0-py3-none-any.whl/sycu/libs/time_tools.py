import time
from datetime import date, datetime, timedelta


def print_timestamp(timestamp):
    print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp / 1000)))


def format_timestamp(timestamp):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp / 1000))


def format_date(timestamp):
    return time.strftime("%Y-%m-%d", time.localtime(timestamp / 1000))


def format_date_to(to_days):
    now = date.today()
    to = now + timedelta(days=to_days)
    return to

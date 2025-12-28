from datetime import datetime as dt, timedelta as td

import pytz

tehran_tz = pytz.timezone("Asia/Tehran")


def duration_to_time(duration_str):
    duration_str = duration_str[2:]
    hours, minutes, seconds = 0, 0, 0
    start = 0
    for i, char in enumerate(duration_str):
        if not char.isdigit():
            end = i
            if char == "H":
                hours = int(duration_str[start:end])
            elif char == "M":
                minutes = int(duration_str[start:end])
            elif char == "S":
                seconds = int(duration_str[start:end])
            start = i + 1
    return td(hours=hours, minutes=minutes, seconds=seconds)


def daily_interval(selected_date):
    end_date = selected_date + td(days=1)
    start_date = selected_date
    e_year, e_month, e_day = end_date.year, end_date.month, end_date.day
    s_year, s_month, s_day = start_date.year, start_date.month, start_date.day
    end = dt(year=e_year, month=e_month, day=e_day, hour=0, minute=0, second=0)
    start = dt(year=s_year, month=s_month, day=s_day, hour=0, minute=0, second=0)
    return [start, end]


def normal2clockify(norm_date):
    return f"{norm_date.strftime('%Y-%m-%dT%H:%M:%SZ')}"


def to_iso_8601_duration(timedelta):
    seconds = int(timedelta.total_seconds())
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    zero = 0
    duration_str = "PT"
    if hours > zero:
        duration_str += f"{hours}H"
    if minutes > zero:
        duration_str += f"{minutes}M"
    if seconds > zero or (hours == zero and minutes == zero):
        duration_str += f"{seconds}S"
    return duration_str


def calculate_duration(time_str):
    utc_time = dt.strptime(time_str, "%Y-%m-%dT%H:%M:%SZ")
    utc_time = utc_time.replace(tzinfo=pytz.utc)
    tehran_time = utc_time.astimezone(tehran_tz)
    now_tehran = dt.now(tehran_tz)
    time_difference = now_tehran - tehran_time
    return time_difference


def get_duration(record):
    if record["timeInterval"]["duration"]:
        return duration_to_time(record["timeInterval"]["duration"])
    else:
        return calculate_duration(record["timeInterval"]["start"])


def days_to_txt(dates_list):
    dates, fulldate_format = [], "%Y-%m-%d (%A)"
    for d in dates_list:
        date_obj = dt.strptime(d, "%Y-%m-%d").date()
        dates.append(date_obj)
    sorted_dates = sorted(dates)
    categories = create_date_categories(sorted_dates)
    text_parts = []
    for category in categories:
        if len(category) > 1:
            start = category[0].strftime(fulldate_format)
            end = category[-1].strftime(fulldate_format)
            text_parts.append(f"{start} to {end}")
        else:
            text_parts.append(category[0].strftime(fulldate_format))
    return " | ".join(text_parts)


def create_date_categories(sorted_dates):
    categories = []
    if not sorted_dates:
        return categories
    current_category = [sorted_dates[0]]
    for date_obj in sorted_dates[1:]:
        prev_date = current_category[-1]
        delta = date_obj - prev_date
        if delta.days == 1:
            current_category.append(date_obj)
        else:
            categories.append(current_category)
            current_category = [date_obj]
    categories.append(current_category)
    return categories

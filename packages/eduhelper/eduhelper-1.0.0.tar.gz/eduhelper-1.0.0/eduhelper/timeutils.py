
from datetime import datetime, date


def _parse_date(date_string):
    
    if not isinstance(date_string, str):
        raise TypeError("Date must be provided as a string")

    try:
        return datetime.strptime(date_string, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("Date format must be YYYY-MM-DD")


def days_left(date_string):
    
    target_date = _parse_date(date_string)
    today = date.today()

    delta = (target_date - today).days
    return max(delta, 0)


def is_urgent(date_string, threshold=3):
    
    if threshold < 0:
        raise ValueError("Threshold must be non-negative")

    return days_left(date_string) <= threshold


def deadline_status(date_string):
    
    remaining = days_left(date_string)

    if remaining == 0:
        return "Deadline is today"
    elif remaining <= 3:
        return "Urgent deadline"
    elif remaining <= 7:
        return "Upcoming deadline"
    return "Deadline is not soon"


def days_between(start_date, end_date):
    
    start = _parse_date(start_date)
    end = _parse_date(end_date)

    return abs((end - start).days)


def _validate_hours(hours):
    
    if not isinstance(hours, (int, float)):
        raise TypeError("Hours must be a number")
    if hours <= 0:
        raise ValueError("Hours must be greater than zero")


def daily_study_plan(hours, break_ratio=0.25):
    
    _validate_hours(hours)

    if not 0 < break_ratio < 1:
        raise ValueError("Break ratio must be between 0 and 1")

    break_time = round(hours * break_ratio, 2)
    study_time = round(hours - break_time, 2)

    return {
        "study_hours": study_time,
        "break_hours": break_time
    }


def pomodoro_sessions(hours):
    
    _validate_hours(hours)

    total_minutes = hours * 60
    session_length = 30  # 25 min study + 5 min break

    return int(total_minutes // session_length)


def study_intensity(hours):
    
    _validate_hours(hours)

    if hours < 1:
        return "Light"
    elif hours < 3:
        return "Moderate"
    elif hours < 6:
        return "High"
    return "Intensive"


def study_recommendation(hours):
    
    intensity = study_intensity(hours)

    recommendations = {
        "Light": "Do light review and revision",
        "Moderate": "Focus on one main topic",
        "High": "Deep study with practice problems",
        "Intensive": "Full study day with scheduled breaks"
    }

    return recommendations[intensity]


def weekly_plan(daily_hours, days=5):
    
    _validate_hours(daily_hours)

    if not isinstance(days, int) or days <= 0:
        raise ValueError("Days must be a positive integer")

    total_hours = round(daily_hours * days, 2)

    return {
        "days": days,
        "daily_hours": daily_hours,
        "total_weekly_hours": total_hours
    }
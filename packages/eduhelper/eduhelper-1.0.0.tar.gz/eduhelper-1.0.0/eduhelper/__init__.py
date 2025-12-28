"""
eduhelper

A beginner-friendly Python library to help students
manage grades, deadlines, and study planning.
"""

from .grades import (
    average_score,
    calculate_gpa,
    weighted_gpa,
    pass_or_fail,
    letter_grade,
    grade_summary
)

from .timeutils import (
    days_left,
    is_urgent,
    deadline_status,
    days_between
)

from .studyplan import (
    daily_study_plan,
    pomodoro_sessions,
    study_intensity,
    study_recommendation,
    weekly_plan
)

all = [
    # grades
    "average_score",
    "calculate_gpa",
    "weighted_gpa",
    "pass_or_fail",
    "letter_grade",
    "grade_summary",

    # timeutils
    "days_left",
    "is_urgent",
    "deadline_status",
    "days_between",

    # studyplan
    "daily_study_plan",
    "pomodoro_sessions",
    "study_intensity",
    "study_recommendation",
    "weekly_plan"
]
def _validate_scores(scores):
    
    if not isinstance(scores, list):
        raise TypeError("Scores must be provided as a list")

    if not scores:
        raise ValueError("Score list cannot be empty")

    for score in scores:
        if not isinstance(score, (int, float)):
            raise TypeError("All scores must be numbers")
        if score < 0:
            raise ValueError("Scores cannot be negative")


def average_score(scores):
    
    _validate_scores(scores)

    total = sum(scores)
    return round(total / len(scores), 2)


def calculate_gpa(grades, scale=5):
    
    _validate_scores(grades)

    if scale <= 0:
        raise ValueError("Scale must be greater than zero")

    gpa = average_score(grades)

    # GPA should not exceed the scale
    return min(gpa, scale)


def weighted_gpa(grades, weights):
    
    _validate_scores(grades)

    if not isinstance(weights, list):
        raise TypeError("Weights must be a list")

    if len(grades) != len(weights):
        raise ValueError("Grades and weights must have the same length")

    if sum(weights) == 0:
        raise ValueError("Sum of weights cannot be zero")

    total = 0
    for grade, weight in zip(grades, weights):
        total += grade * weight

    return round(total / sum(weights), 2)


def pass_or_fail(score, pass_mark=3):
    
    if score >= pass_mark:
        return "Pass"
    return "Fail"


def letter_grade(score):
    
    if score >= 4.5:
        return "A"
    elif score >= 3.5:
        return "B"
    elif score >= 2.5:
        return "C"
    elif score >= 2:
        return "D"
    return "F"


def grade_summary(scores):
    
    _validate_scores(scores)

    return {
        "average": average_score(scores),
        "minimum": min(scores),
        "maximum": max(scores)
    }
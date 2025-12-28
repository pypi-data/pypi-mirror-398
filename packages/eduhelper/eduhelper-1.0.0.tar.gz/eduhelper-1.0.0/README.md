# eduhelper 📚

eduhelper is a beginner-friendly Python library designed to help students
manage their academic life using simple and practical tools.

# Designer
Name & Family: Mani Eyvazi 
Uni: RUDN
student Nu.: 1032245107

## Features

### 🎓 Grades
- Calculate average score
- GPA calculation (normal & weighted)
- Pass / Fail check
- Letter grade conversion
- Grade statistics summary

### ⏰ Time Utilities
- Days left until a deadline
- Urgency detection
- Deadline status messages
- Days between two dates

### 📖 Study Planning
- Daily study & break planning
- Pomodoro session calculation
- Study intensity evaluation
- Study recommendations
- Weekly study plan

---

## Installation

This library does not require installation.
Just place the eduhelper folder in your project directory.

---

## Usage Example

`python
import eduhelper

scores = [4, 3.5, 5]

print(eduhelper.average_score(scores))
print(eduhelper.calculate_gpa(scores))
print(eduhelper.letter_grade(4.2))
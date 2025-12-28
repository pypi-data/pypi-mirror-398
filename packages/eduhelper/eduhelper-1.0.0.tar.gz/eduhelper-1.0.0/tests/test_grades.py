import unittest
from eduhelper.grades import (
    average_score,
    calculate_gpa,
    weighted_gpa,
    pass_or_fail,
    letter_grade,
    grade_summary
)

class TestGrades(unittest.TestCase):

    def test_average_score(self):
        self.assertEqual(average_score([4, 5, 3]), 4.0)
        with self.assertRaises(ValueError):
            average_score([])

    def test_calculate_gpa(self):
        self.assertEqual(calculate_gpa([4, 3, 5]), 4.0)
        with self.assertRaises(ValueError):
            calculate_gpa([])

    def test_weighted_gpa(self):
        self.assertEqual(weighted_gpa([4, 3, 5], [2, 3, 5]), 4.2)
        with self.assertRaises(ValueError):
            weighted_gpa([4,5], [1])

    def test_pass_or_fail(self):
        self.assertEqual(pass_or_fail(4), "Pass")
        self.assertEqual(pass_or_fail(2.5), "Fail")

    def test_letter_grade(self):
        self.assertEqual(letter_grade(4.6), "A")
        self.assertEqual(letter_grade(3.8), "B")
        self.assertEqual(letter_grade(2.2), "D")
        self.assertEqual(letter_grade(1.5), "F")

    def test_grade_summary(self):
        summary = grade_summary([3,4,5])
        self.assertEqual(summary["average"], 4.0)
        self.assertEqual(summary["minimum"], 3)
        self.assertEqual(summary["maximum"], 5)

if __name__ == "__main__":
    unittest.main()
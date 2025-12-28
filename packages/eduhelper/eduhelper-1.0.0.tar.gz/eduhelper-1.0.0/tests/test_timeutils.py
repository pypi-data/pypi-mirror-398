import unittest
from datetime import date, timedelta
from eduhelper.timeutils import days_left, is_urgent, deadline_status, days_between

class TestTimeUtils(unittest.TestCase):

    def setUp(self):
        self.today = date.today()
        self.tomorrow = (self.today + timedelta(days=1)).strftime("%Y-%m-%d")
        self.future = (self.today + timedelta(days=10)).strftime("%Y-%m-%d")
        self.past = (self.today - timedelta(days=5)).strftime("%Y-%m-%d")

    def test_days_left(self):
        self.assertEqual(days_left(self.tomorrow), 1)
        self.assertEqual(days_left(self.past), 0)

    def test_is_urgent(self):
        self.assertTrue(is_urgent(self.tomorrow, threshold=2))
        self.assertFalse(is_urgent(self.future, threshold=3))

    def test_deadline_status(self):
        self.assertEqual(deadline_status(self.tomorrow), "Urgent deadline")
        self.assertEqual(deadline_status(self.future), "Deadline is not soon")

    def test_days_between(self):
        self.assertEqual(days_between(self.today.strftime("%Y-%m-%d"), self.future), 10)
        self.assertEqual(days_between(self.future, self.today.strftime("%Y-%m-%d")), 10)

if __name__ == "__main__":
    unittest.main()
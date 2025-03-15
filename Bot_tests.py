import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from main_bot import ReminderBot as task_bot


##automated
class TestReminderBot(unittest.TestCase):

    def setUp(self):
        self.bot = task_bot('6378396356:AAH2_xlsgS7vSXyv9lG3aJd2eCIqRglfD8M')
        self.chat_id = 123456789
        self.task = "Buy groceries"
        self.timing = "today at 10:00 AM"

    def test_parse_timing_today(self):
        parsed_datetime = self.bot.parse_timing("today at 10:00 AM")
        expected_datetime = datetime.combine(datetime.now().date(), datetime.strptime("10:00 AM", "%I:%M %p").time())
        self.assertEqual(parsed_datetime, expected_datetime)

    def test_parse_timing_tomorrow(self):
        tomorrow = datetime.now() + timedelta(days=1)
        parsed_datetime = self.bot.parse_timing("tomorrow at 10:00 AM")
        expected_datetime = datetime.combine(tomorrow.date(), datetime.strptime("10:00 AM", "%I:%M %p").time())
        self.assertEqual(parsed_datetime, expected_datetime)

    def test_parse_timing_invalid(self):
        parsed_datetime = self.bot.parse_timing("invalid timing")
        self.assertIsNone(parsed_datetime)

    @patch('mainAct.Bot')
    def test_send_reminder(self, mock_bot):
        self.bot.send_reminder(self.chat_id, self.task)
        mock_bot.return_value.send_message.assert_called_with(chat_id=self.chat_id,
                                                              text=f"🔶 REMINDER: Don't forget to {self.task}!")

    def test_clear_task_result_with_at(self):
        task = "Buy groceries at 10:00 AM"
        cleared_task = self.bot.clear_task_result(task)
        self.assertEqual(cleared_task, "Buy groceries")

    def test_clear_task_result_without_at(self):
        task = "Buy groceries"
        cleared_task = self.bot.clear_task_result(task)
        self.assertEqual(cleared_task, "Buy groceries")


if __name__ == '__main__':
    unittest.main()

import unittest
from unittest.mock import patch, MagicMock

from wallypub.utils.date import get_string_date


class TestGetStringDate(unittest.TestCase):
    @patch("datetime.date")  # Patch the datetime module
    def test_get_string_date(self, mock_datetime):
        """Tests the get_string_date function."""

        mock_date_instance = MagicMock()
        mock_date_instance.strftime.return_value = "January 31, 2024"
        mock_datetime.today.return_value = mock_date_instance

        expected_date_string = "January 31, 2024"
        actual_date_string = get_string_date()
        self.assertEqual(expected_date_string, actual_date_string)


if __name__ == "__main__":
    unittest.main()

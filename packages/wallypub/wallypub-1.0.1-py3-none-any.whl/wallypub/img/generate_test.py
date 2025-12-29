import unittest
from unittest.mock import patch
import os

from wallypub.img.generate import CoverGenerator


class TestCoverGenerator(unittest.TestCase):
    @patch("img.generate.get_string_date")
    @patch("img.generate.get_random_color")
    @patch("img.generate.get_hex_value")
    @patch("img.generate.return_complimentary_color")
    @patch("img.generate.Image")
    @patch("img.generate.ImageDraw")
    @patch("img.generate.ImageFont")
    def test_generate_default_mocked(
        self,
        mock_image_font,
        mock_image_draw,
        mock_image,
        mock_return_complimentary_color,
        mock_get_hex_value,
        mock_get_random_color,
        mock_get_string_date,
    ):
        # Setup mocks
        mock_get_string_date.return_value = "October 2025"
        mock_get_random_color.return_value = (10, 20, 30)
        mock_get_hex_value.return_value = "#0a141e"
        mock_return_complimentary_color.return_value = (245, 235, 225)

        generator = CoverGenerator()

        generator.generate_default()
        generator.save()

        mock_image.new.assert_called_once_with(
            "RGB", size=(900, 1440), color=(10, 20, 30)
        )
        self.assertIsNotNone(generator.image)

    @patch("img.generate.get_string_date")
    def test_generate_real_image(self, mock_get_string_date):
        # Arrange
        mock_get_string_date.return_value = "October 1, 2025"

        # Clean up previous test runs
        if os.path.exists("/tmp/test_cover.png"):
            os.remove("/tmp/test_cover.png")

        generator = CoverGenerator()

        # Act
        generator.generate_default()


if __name__ == "__main__":
    unittest.main()

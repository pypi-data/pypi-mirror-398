import unittest
from unittest.mock import patch
from dataclasses import dataclass
from typing import List

import platformdirs

from wallypub.conf.constants import APP_NAME, APP_AUTHOR_NAME
from wallypub.epub_builder.create import (
    avoid_file_collisions,
    initialize_epub,
    get_file_title,
)

test_static_cover = platformdirs.user_data_dir(APP_NAME, APP_AUTHOR_NAME) + "/static"


class TestAvoidFileCollisions(unittest.TestCase):
    @patch("epub_builder.create.cfg")
    @patch("epub_builder.create.glob.glob")
    def test_avoid_file_collisions(self, mock_glob, mock_config):
        mock_config.output_path = "./digest"

        @dataclass
        class TestCase:
            name: str
            mock_glob_return: List[str]
            file_title_input: str
            expected_file_title: str

        testcases = [
            TestCase(
                name="no matching files",
                mock_glob_return=[],
                file_title_input="Wallypub Presents_20250726",
                expected_file_title="Wallypub Presents_20250726",
            ),
            TestCase(
                name="one matching file",
                mock_glob_return=["./digest/Wallypub Presents_20250726.epub"],
                file_title_input="Wallypub Presents_20250726",
                expected_file_title="Wallypub Presents_20250726-1",
            ),
            TestCase(
                name="n matching files",
                mock_glob_return=[
                    "./digest/Wallypub Presents_20250726.epub",
                    "./digest/Wallypub Presents_20250726-1.epub",
                    "./digest/Wallypub Presents_20250726-2.epub",
                ],
                file_title_input="Wallypub Presents_20250726",
                expected_file_title="Wallypub Presents_20250726-3",
            ),
            TestCase(
                name="10 or more matching files",
                mock_glob_return=[
                    "./digest/Wallypub Presents_20250726.epub",
                    "./digest/Wallypub Presents_20250726-1.epub",
                    "./digest/Wallypub Presents_20250726-2.epub",
                    "./digest/Wallypub Presents_20250726-3.epub",
                    "./digest/Wallypub Presents_20250726-4.epub",
                    "./digest/Wallypub Presents_20250726-5.epub",
                    "./digest/Wallypub Presents_20250726-6.epub",
                    "./digest/Wallypub Presents_20250726-7.epub",
                    "./digest/Wallypub Presents_20250726-9.epub",
                    "./digest/Wallypub Presents_20250726-10.epub",
                ],
                file_title_input="Wallypub Presents_20250726",
                expected_file_title="Wallypub Presents_20250726-11",
            ),
        ]
        for case in testcases:
            with self.subTest(name=case.name):
                mock_glob.return_value = case.mock_glob_return
                actual_title = avoid_file_collisions(case.file_title_input)
                self.assertEqual(actual_title, case.expected_file_title)


class TestCreate(unittest.TestCase):
    @patch("epub_builder.create.date")
    @patch("epub_builder.create.cfg")
    def test_get_file_title(self, mock_config, mock_date):
        mock_config.title = "Test digest"
        mock_date.strftime.return_value = "20250101"
        result = get_file_title()
        self.assertEqual(result, "Test digest_20250101")

    @patch("pypub.Epub")
    @patch("img.CoverGenerator")
    @patch("epub_builder.create.get_string_date")
    @patch("epub_builder.create.cfg")
    def test_initialize_epub(
        self, mock_config, mock_get_string_date, mock_cover_generator, mock_epub
    ):
        @dataclass
        class TestCase:
            name: str
            cover_path: str
            expected_generator_calls: int

        testcases = [
            TestCase(
                name="default cover",
                cover_path="cover.jpg",
                expected_generator_calls=1,
            ),
            TestCase(
                name="custom cover",
                cover_path="custom_cover.png",
                expected_generator_calls=0,
            ),
        ]

        for case in testcases:
            with self.subTest(name=case.name):
                # Reset mocks for each run
                mock_cover_generator.reset_mock()
                mock_generator_instance = mock_cover_generator.return_value

                mock_config.filepath = test_static_cover
                mock_config.cover_file = case.cover_path
                mock_config.title = "My Test Digest"
                mock_config.author = "Test Author"
                mock_get_string_date.return_value = "January 1, 2025"

                initialize_epub()

                self.assertEqual(
                    mock_cover_generator.call_count, case.expected_generator_calls
                )
                if case.expected_generator_calls > 0:
                    mock_generator_instance.generate_default.assert_called_once()
                mock_epub.assert_called_once()
                mock_epub.reset_mock()  # Reset for next iteration


if __name__ == "__main__":
    unittest.main()

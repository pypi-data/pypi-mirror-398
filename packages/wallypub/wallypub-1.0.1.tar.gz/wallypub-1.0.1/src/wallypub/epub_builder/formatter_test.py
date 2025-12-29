import unittest
from unittest.mock import patch, MagicMock
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from wallypub.epub_builder.formatter import (
    add_article_info,
    merge_entries_to_chapters,
    ENTRY_STYLES,
)


class TestAddArticleInfo(unittest.TestCase):
    def test_add_article_info(self):
        @dataclass
        class TestCase:
            name: str
            author: str | List[str]
            published_by: str
            date: str
            link: str
            # We will check for smaller, more specific parts to avoid brittleness
            expected_substrings: List[str]

        testcases = [
            TestCase(
                name="single author",
                author="John Doe",
                published_by="A Publisher",
                date="2025-01-01",
                link="http://example.com",
                expected_substrings=[
                    'id="author">John Doe</span>',
                    'id="published_by">A Publisher</span>',
                    'id="date">2025-01-01</span>',
                    'href="http://example.com"',
                ],
            ),
            TestCase(
                name="multiple authors",
                author=["John Doe", "Jane Smith"],
                published_by="Another Publisher",
                date="2025-01-02",
                link="http://example.com/2",
                expected_substrings=[
                    'id="author">John Doe, Jane Smith</span>',
                    'id="published_by">Another Publisher</span>',
                ],
            ),
            TestCase(
                name="missing info",
                author="",
                published_by="",
                date="",
                link="",
                expected_substrings=[
                    'id="author"></span>',
                    'id="published_by"></span>',
                    'id="date"></span>',
                    'href=""',
                ],
            ),
        ]

        for case in testcases:
            with self.subTest(name=case.name):
                html_output = add_article_info(
                    case.author, case.published_by, case.date, case.link
                )
                for substring in case.expected_substrings:
                    self.assertIn(substring, html_output)


class TestMergeEntriesToChapters(unittest.TestCase):
    @patch("pypub.create_chapter_from_html")
    def test_merge_entries_to_chapters(self, mock_create_chapter):
        # Mock the return value of create_chapter_from_html to be a simple object
        mock_chapter = MagicMock()
        mock_create_chapter.return_value = mock_chapter

        # A mock content processor for testing
        def mock_processor(entry):
            return f"Processed: {entry['content']}"

        @dataclass
        class TestCase:
            name: str
            entries: List[Dict[str, Any]]
            style_kwargs: Dict[str, Any]
            expected_calls: int
            expected_html_content: Optional[str] = None
            expected_info_substring: Optional[str] = None

        testcases = [
            TestCase(
                name="wallabag style without processor",
                entries=[
                    {
                        "title": "T1",
                        "content": "C1",
                        "published_by": "P1",
                        "published_at": "D1",
                        "url": "U1",
                    }
                ],
                style_kwargs=ENTRY_STYLES["wallabag"],
                expected_calls=1,
                expected_html_content="C1",
            ),
            TestCase(
                name="empty entry list",
                entries=[],
                style_kwargs=ENTRY_STYLES["wallabag"],
                expected_calls=0,
            ),
            TestCase(
                name="empty entry list",
                entries=[],
                style_kwargs=ENTRY_STYLES["wallabag"],
                expected_calls=0,
                expected_html_content=None,
                expected_info_substring=None,
            ),
        ]

        for case in testcases:
            with self.subTest(name=case.name):
                mock_digest = MagicMock()
                mock_create_chapter.reset_mock()

                merge_entries_to_chapters(
                    mock_digest, case.entries, **case.style_kwargs
                )

                self.assertEqual(
                    mock_digest.add_chapter.call_count, case.expected_calls
                )
                if case.expected_calls > 0:
                    call_args, _ = mock_create_chapter.call_args
                    html_bytes = call_args[0]
                    html_string = html_bytes.decode("utf-8")
                    self.assertIn(case.expected_html_content, html_string)


if __name__ == "__main__":
    unittest.main()

import unittest
from unittest import TestCase, mock

from wallypub.services.wallabag import Wallabag

from dataclasses import dataclass
from typing import Any, Dict, List


class TestWallabag(TestCase):
    @mock.patch("http.client.HTTPSConnection")  # Mock the HTTPSConnection
    def test_authenticate(self, MockHTTPSConnection):
        # Create a mock response object
        mock_response = mock.MagicMock()
        mock_response.read.return_value = (
            b'{"access_token": "mocked_token", "expires_in": 3600}'
        )
        mock_response.status = 200  # Set a successful status code

        # Set up the mock connection
        mock_conn = MockHTTPSConnection.return_value
        mock_conn.getresponse.return_value = mock_response

        # Create an instance of your authenticator class
        authenticator = Wallabag()
        authenticator.wallabag_url = "wallabag.example.com"  # Set a test URL

        # Call the authenticate method
        authenticator.authenticate()

        # Assertions
        MockHTTPSConnection.assert_called_once_with("wallabag.example.com")
        mock_conn.request.assert_called_once()
        self.assertEqual(mock_response.status, 200)

    @mock.patch("http.client.HTTPSConnection")
    def test_get_entry(self, MockHTTPSConnection):
        @dataclass
        class GetEntryTestCase:
            name: str
            entry_id: str
            mock_status: int
            mock_response_data: bytes
            expected_result: Dict[str, Any]
            expected_url_path: str
            side_effect: Any = None

        test_cases = [
            GetEntryTestCase(
                name="success: retrieve existing entry",
                entry_id="123",
                mock_status=200,
                mock_response_data=b'{"id": 123, "title": "Test Entry"}',
                expected_result={"id": 123, "title": "Test Entry"},
                expected_url_path="/api/entries/123",
            ),
            GetEntryTestCase(
                name="failure: entry not found (404)",
                entry_id="999",
                mock_status=404,
                mock_response_data=b'{"error": "Entry not found"}',
                expected_result={"error": "Entry not found"},
                expected_url_path="/api/entries/999",
            ),
            GetEntryTestCase(
                name="error: server returns 500",
                entry_id="123",
                mock_status=500,
                mock_response_data=b'{"error": "Internal Server Error"}',
                expected_result={"error": "Internal Server Error"},
                expected_url_path="/api/entries/123",
            ),
        ]

        for case in test_cases:
            with self.subTest(msg=case.name):
                # Create a mock response object
                mock_response = mock.MagicMock()
                mock_response.read.return_value = case.mock_response_data
                mock_response.status = case.mock_status
                mock_response.reason = "OK" if case.mock_status == 200 else "Error"

                # Set up the mock connection
                mock_conn = MockHTTPSConnection.return_value
                mock_conn.getresponse.return_value = mock_response

                # Set side_effect for request if an exception is expected
                if case.side_effect:
                    mock_conn.request.side_effect = case.side_effect
                else:
                    mock_conn.request.side_effect = (
                        None  # Clear side effect for other tests
                    )

                # Create an instance of Wallabag and set necessary attributes
                wallabag_instance = Wallabag()
                wallabag_instance.wallabag_url = "wallabag.example.com"
                wallabag_instance.bearer_token = "mocked_bearer_token"

                # Call the get_entry method
                actual_result = wallabag_instance.get_entry(case.entry_id)

                # Assertions
                MockHTTPSConnection.assert_called_with("wallabag.example.com")
                mock_conn.request.assert_called_with(
                    "GET",
                    case.expected_url_path,
                    headers={
                        "accept": "*/*",
                        "Authorization": "Bearer mocked_bearer_token",
                    },
                )
                self.assertEqual(actual_result, case.expected_result)

                # Reset mocks for the next subtest
                MockHTTPSConnection.reset_mock()

    @mock.patch("http.client.HTTPSConnection")
    def test_get_entries(self, MockHTTPSConnection):
        @dataclass
        class GetEntriesTestCase:
            name: str
            params: Dict[str, Any]
            mock_status: int
            mock_response_data: bytes
            expected_result: List[Dict[str, Any]]
            expected_url_path: str
            side_effect: Any = None

        test_cases = [
            GetEntriesTestCase(
                name="success: retrieve all entries",
                params={},
                mock_status=200,
                mock_response_data=b'[{"id": 1, "title": "Entry 1"}, {"id": 2, "title": "Entry 2"}]',
                expected_result=[
                    {"id": 1, "title": "Entry 1"},
                    {"id": 2, "title": "Entry 2"},
                ],
                expected_url_path="/api/entries?",
            ),
            GetEntriesTestCase(
                name="success: retrieve starred entries",
                params={"starred": "1"},
                mock_status=200,
                mock_response_data=b'[{"id": 3, "title": "Starred Entry"}]',
                expected_result=[{"id": 3, "title": "Starred Entry"}],
                expected_url_path="/api/entries?starred=1",
            ),
            GetEntriesTestCase(
                name="success: retrieve entries with tags and domain",
                params={"tags": "python", "domain_name": "example.com"},
                mock_status=200,
                mock_response_data=b'[{"id": 4, "title": "Python Example"}]',
                expected_result=[{"id": 4, "title": "Python Example"}],
                expected_url_path="/api/entries?tags=python&domain_name=example.com",
            ),
            GetEntriesTestCase(
                name="success: no entries found",
                params={"starred": "1", "tags": "nonexistent"},
                mock_status=200,
                mock_response_data=b"[]",
                expected_result=[],
                expected_url_path="/api/entries?starred=1&tags=nonexistent",
            ),
            GetEntriesTestCase(
                name="error: server returns 500",
                params={},
                mock_status=500,
                mock_response_data=b'[{"error": "Internal Server Error"}]',
                expected_result=[{"error": "Internal Server Error"}],
                expected_url_path="/api/entries?",
            ),
        ]

        for case in test_cases:
            with self.subTest(msg=case.name):
                # Create a mock response object
                mock_response = mock.MagicMock()
                mock_response.read.return_value = case.mock_response_data
                mock_response.status = case.mock_status
                mock_response.reason = "OK" if case.mock_status == 200 else "Error"

                # Set up the mock connection
                mock_conn = MockHTTPSConnection.return_value
                mock_conn.getresponse.return_value = mock_response

                # Set side_effect for request if an exception is expected
                if case.side_effect:
                    mock_conn.request.side_effect = case.side_effect
                else:
                    mock_conn.request.side_effect = (
                        None  # Clear side effect for other tests
                    )

                # Create an instance of Wallabag and set necessary attributes
                wallabag_instance = Wallabag()
                wallabag_instance.wallabag_url = "wallabag.example.com"
                wallabag_instance.bearer_token = "mocked_bearer_token"

                # Call the get_entries method
                actual_result = wallabag_instance.get_entries(case.params)

                # Assertions
                MockHTTPSConnection.assert_called_with("wallabag.example.com")
                mock_conn.request.assert_called_with(
                    "GET",
                    case.expected_url_path,
                    headers={
                        "accept": "*/*",
                        "Authorization": "Bearer mocked_bearer_token",
                    },
                )
                self.assertEqual(actual_result, case.expected_result)

                # Reset mocks for the next subtest
                MockHTTPSConnection.reset_mock()

    def test_append_url_params(self):
        @dataclass
        class AppendUrlParamsTestCase:
            name: str
            input_params: Dict[str, Any]
            expected: str

        wally = Wallabag()
        testcases = [
            AppendUrlParamsTestCase(
                name="success: single param",
                input_params={
                    "starred": "1",
                    "sort": "",
                    "order": "",
                    "page": "",
                    "perPage": "",
                    "tags": "",
                    "since": "",
                    "public": "",
                    "detail": "",
                    "domain_name": "",
                },
                expected="?starred=1",
            ),
            AppendUrlParamsTestCase(
                name="success: three params",
                input_params={
                    "archive": "0",
                    "starred": "1",
                    "sort": "",
                    "order": "",
                    "page": "",
                    "perPage": "",
                    "tags": "api",
                    "since": "",
                    "public": "",
                    "detail": "",
                    "domain_name": "wikipedia.com",
                },
                expected="?archive=0&starred=1&tags=api&domain_name=wikipedia.com",
            ),
            AppendUrlParamsTestCase(
                name="success: empty params",
                input_params={},
                expected="?",
            ),
            AppendUrlParamsTestCase(
                name="success: all empty string params",
                input_params={
                    "starred": "",
                    "sort": "",
                },
                expected="?",
            ),
            AppendUrlParamsTestCase(
                name="success: mixed empty and valid params",
                input_params={
                    "starred": "",
                    "sort": "title",
                    "order": "",
                    "page": "1",
                },
                expected="?sort=title&page=1",
            ),
        ]

        for case in testcases:
            with self.subTest(msg=case.name):
                actual_param_str = wally.append_url_params(case.input_params)
                self.assertEqual(
                    case.expected,
                    actual_param_str,
                    f"failed test {case.name} expected {case.expected}, actual {actual_param_str}",
                )

    @mock.patch("http.client.HTTPSConnection")
    def test_patch_entry(self, MockHTTPSConnection):
        @dataclass
        class PatchEntryTestCase:
            name: str
            entry_id: str
            body: Dict[str, Any]
            mock_status: int
            mock_response_data: bytes
            expected_result: Dict[str, Any]
            expected_request_body: str

        test_cases = [
            PatchEntryTestCase(
                name="success: mark as read",
                entry_id="123",
                body={"archive": 1},
                mock_status=200,
                mock_response_data=b'{"id": 123, "is_archived": true}',
                expected_result={"id": 123, "is_archived": True},
                expected_request_body='{"archive": 1}',
            ),
            PatchEntryTestCase(
                name="success: add tags",
                entry_id="456",
                body={"tags": ["python", "testing"]},
                mock_status=200,
                mock_response_data=b'{"id": 456, "tags": ["python", "testing"]}',
                expected_result={"id": 456, "tags": ["python", "testing"]},
                expected_request_body='{"tags": ["python", "testing"]}',
            ),
            PatchEntryTestCase(
                name="failure: entry not found",
                entry_id="999",
                body={"archive": 1},
                mock_status=404,
                mock_response_data=b'{"error": "Entry not found"}',
                expected_result={"error": "Entry not found"},
                expected_request_body='{"archive": 1}',
            ),
            PatchEntryTestCase(
                name="failure: invalid input",
                entry_id="123",
                body={"invalid_field": "value"},
                mock_status=400,
                mock_response_data=b'{"error": "Invalid input"}',
                expected_result={"error": "Invalid input"},
                expected_request_body='{"invalid_field": "value"}',
            ),
        ]

        for case in test_cases:
            with self.subTest(msg=case.name):
                mock_response = mock.MagicMock()
                mock_response.read.return_value = case.mock_response_data
                mock_response.status = case.mock_status
                mock_response.reason = "OK" if case.mock_status == 200 else "Error"

                mock_conn = MockHTTPSConnection.return_value
                mock_conn.getresponse.return_value = mock_response

                wallabag_instance = Wallabag()
                wallabag_instance.wallabag_url = "wallabag.example.com"
                wallabag_instance.bearer_token = "mocked_bearer_token"

                actual_result = wallabag_instance.patch_entry(case.entry_id, case.body)

                MockHTTPSConnection.assert_called_with("wallabag.example.com")
                mock_conn.request.assert_called_with(
                    "PATCH",
                    f"/api/entries/{case.entry_id}",
                    body=case.expected_request_body,
                    headers={
                        "accept": "*/*",
                        "Authorization": "Bearer mocked_bearer_token",
                        "content-type": "application/json",
                    },
                )
                self.assertEqual(actual_result, case.expected_result)

                # Reset mocks for the next subtest
                MockHTTPSConnection.reset_mock()


if __name__ == "__main__":
    unittest.main()

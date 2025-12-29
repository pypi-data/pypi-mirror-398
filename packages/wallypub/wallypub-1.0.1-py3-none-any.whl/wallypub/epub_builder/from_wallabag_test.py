import json
import os
from unittest import TestCase

from wallypub.epub_builder.from_wallabag import (
    filter_empty_articles,
    entry_in_array,
    filter_duplicate_articles,
    filter_on_read_times,
    within_read_times,
)

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_TEST_ENTRIES_INPUT_FILE = os.path.join(
    _TEST_DIR, "test_input", "wbag_entries_input.json"
)


class Test(TestCase):
    def test_filter_empty_articles(self):
        test_data_file = open(_TEST_ENTRIES_INPUT_FILE, "r")
        contents = test_data_file.read()
        test_data_file.close()
        json_data = json.loads(contents)

        filtered_entries, empty_entries = filter_empty_articles(
            json_data["_embedded"]["items"]
        )
        if len(filtered_entries) == 1:
            pass

        if len(empty_entries) == 0:
            pass

    def test_entry_in_array(self):
        test_data_file = open(_TEST_ENTRIES_INPUT_FILE, "r")
        contents = test_data_file.read()
        test_data_file.close()
        entry = [
            {
                "is_archived": 0,
                "is_starred": 0,
                "user_name": "person",
                "user_email": "person@example.com",
                "user_id": 123456,
                "tags": [],
                "is_public": False,
                "id": 20266258,
                "title": "‘Cranky’ Opossum Lands in Hospital After Eating Costco Bakery Item",
                "url": "https://www.msn.com/en-us/health/wellness/cranky-opossum-lands-in-hospital-after-eating-costco-bakery-item/ar-AA1z5c2E",
                "hashed_url": "a08aed2ed1924cef29945fc2dc3ede73dd6e76e1",
                "given_url": "https://www.msn.com/en-us/health/wellness/cranky-opossum-lands-in-hospital-after-eating-costco-bakery-item/ar-AA1z5c2E",
                "hashed_given_url": "a08aed2ed1924cef29945fc2dc3ede73dd6e76e1",
                "content": "",
                "created_at": "2025-02-15T12:55:34+0100",
                "updated_at": "2025-02-15T12:55:34+0100",
                "published_at": "2025-02-14T21:41:37+0100",
                "published_by": ["Declan Gallagher"],
                "annotations": [],
                "mimetype": "text/html; charset=UTF-8",
                "reading_time": 4,
                "domain_name": "www.msn.com",
                "preview_picture": "https://img-s-msn-com.akamaized.net/tenant/amp/entityid/AA1z5exS.img?w=1200&h=800&m=4&q=89",
                "http_status": "200",
                "headers": {
                    "cache-control": "no-store",
                    "pragma": "no-cache",
                    "transfer-encoding": "chunked",
                    "content-type": "text/html; charset=UTF-8",
                    "vary": "Accept-Encoding",
                    "set-cookie": "_C_ETH=1; domain=.msn.com; path=/; secure; httponly, _C_Auth=, USRLOC=; expires=Mon, 15 Feb 2027 11:55:34 GMT; domain=.msn.com; path=/; secure; samesite=none; httponly, MUID=0507018927676A4C38EC141D26EC6B74; expires=Thu, 12 Mar 2026 11:55:34 GMT; domain=.msn.com; path=/; secure; samesite=none, MUIDB=0507018927676A4C38EC141D26EC6B74; expires=Thu, 12 Mar 2026 11:55:34 GMT; path=/; httponly, _EDGE_S=F=1&SID=17C04751FDA262991F8C52C5FCF363C0; domain=.msn.com; path=/; httponly, _EDGE_V=1; expires=Thu, 12 Mar 2026 11:55:34 GMT; domain=.msn.com; path=/; httponly",
                    "access-control-allow-methods": "HEAD,GET,OPTIONS",
                    "accept-ch": "Sec-CH-UA-Arch, Sec-CH-UA-Bitness, Sec-CH-UA-Full-Version, Sec-CH-UA-Full-Version-List, Sec-CH-UA-Mobile, Sec-CH-UA-Model, Sec-CH-UA-Platform, Sec-CH-UA-Platform-Version, Sec-CH-Prefers-Color-Scheme, UA-Bitness, UA-Arch, UA-Full-Version, UA-Mobile, UA-Model, UA-Platform-Version, UA-Platform, UA",
                    "content-security-policy": "block-all-mixed-content;connect-src 'self' data: 'unsafe-inline' 'unsafe-eval' https: blob: wss:;default-src 'self' data: 'unsafe-inline' 'unsafe-eval' https: blob: wss: 'report-sample';font-src 'self' data: https: blob: wss: assets.msn.com assets2.msn.com assets.msn.cn assets2.msn.cn;frame-ancestors 'self' int1.msn.com ntp.msn.cn ntp.msn.com windows-int1.msn.com windows.msn.cn windows.msn.com www.bing.com www.msn.com mathsolver.microsoft.com mathsolver-dev.microsoft.com chrome-extension://lklfbkdigihjaaeamncibechhgalldgl *.office.com;media-src 'self' https: blob:;report-to csp-endpoint;worker-src 'self' https: blob: 'report-sample';",
                    "x-content-type-options": "nosniff",
                    "x-fabric-cluster": "pmeprodneu",
                    "x-frame-options": "SAMEORIGIN",
                    "x-ua-compatible": "IE=Edge;chrome=1",
                    "x-xss-protection": "1",
                    "sw-cache-control": "no-store",
                    "nel": '{"report_to":"network-errors","max_age":604800,"success_fraction":0.001,"failure_fraction":0.5}',
                    "report-to": '{"group":"network-errors","max_age":604800,"endpoints":[{"url":"https://deff.nelreports.net/api/report?cat=msn"}]},{"group":"csp-endpoint","max_age":86400,"endpoints":[{"url":"https://deff.nelreports.net/api/report"}]}',
                    "x-ceto-ref": "67b080b68389416584b3d0fef9710809|AFD:51DF6DDA8D7C4966811774D83FB9396C|2025-02-15T11:55:34.659Z",
                    "x-cache": "CONFIG_NOCACHE",
                    "x-msedge-ref": "Ref A: 51DF6DDA8D7C4966811774D83FB9396C Ref B: FRA31EDGE0515 Ref C: 2025-02-15T11:55:34Z",
                    "date": "Sat, 15 Feb 2025 11:55:34 GMT",
                },
                "_links": {"self": {"href": "/api/entries/20266258"}},
            },
        ]
        existing_entries = json.loads(contents)
        if entry_in_array(entry[0], existing_entries["_embedded"]["items"]):
            pass

    def test_filter_duplicate_articles(self):
        test_cases = [
            {
                "name": "empty_list",
                "entries": [],
                "expected_unique": [],
                "expected_duplicates": [],
            },
            {
                "name": "no_duplicates",
                "entries": [
                    {"id": 1, "title": "Article 1"},
                    {"id": 2, "title": "Article 2"},
                    {"id": 3, "title": "Article 3"},
                ],
                "expected_unique": [
                    {"id": 1, "title": "Article 1"},
                    {"id": 2, "title": "Article 2"},
                    {"id": 3, "title": "Article 3"},
                ],
                "expected_duplicates": [],
            },
            {
                "name": "with_duplicates",
                "entries": [
                    {"id": 1, "title": "Article 1"},
                    {"id": 2, "title": "Article 2"},
                    {"id": 1, "title": "Article 1"},
                    {"id": 3, "title": "Article 3"},
                    {"id": 2, "title": "Article 2"},
                ],
                "expected_unique": [
                    {"id": 1, "title": "Article 1"},
                    {"id": 2, "title": "Article 2"},
                    {"id": 3, "title": "Article 3"},
                ],
                "expected_duplicates": [
                    {"id": 1, "title": "Article 1"},
                    {"id": 2, "title": "Article 2"},
                ],
            },
            {
                "name": "all_duplicates",
                "entries": [
                    {"id": 1, "title": "Article 1"},
                    {"id": 1, "title": "Article 1"},
                    {"id": 1, "title": "Article 1"},
                ],
                "expected_unique": [{"id": 1, "title": "Article 1"}],
                "expected_duplicates": [
                    {"id": 1, "title": "Article 1"},
                    {"id": 1, "title": "Article 1"},
                ],
            },
        ]

        for test_case in test_cases:
            with self.subTest(name=test_case["name"]):
                unique_entries, duplicate_entries = filter_duplicate_articles(
                    test_case["entries"]
                )
                self.assertEqual(unique_entries, test_case["expected_unique"])
                self.assertEqual(duplicate_entries, test_case["expected_duplicates"])

    """
    The read time tests rely on the defaults found in conf/app.py
    minimum_read_time = 0 
    max_read_time = 120
    """

    def test_filter_on_read_times(self):
        test_data_file = open(_TEST_ENTRIES_INPUT_FILE, "r")
        contents = test_data_file.read()
        test_data_file.close()
        json_data = json.loads(contents)

        bounded_entries, unbounded_entries = filter_on_read_times(
            json_data["_embedded"]["items"]
        )

        if len(bounded_entries) == 1:
            pass

        if len(unbounded_entries) == 2:
            pass

    def test_within_read_times(self):
        test_cases = [
            {
                "name": "within bounds",
                "entry": {"id": 1, "title": "Article 1", "reading_time": "5"},
                "want": True,
            },
            {
                "name": "out of bounds",
                "entry": {"id": 1, "title": "Article 1", "reading_time": "200"},
                "want": False,
            },
            {
                "name": "empty article",
                "entry": {"id": 1, "title": "Article 1", "reading_time": "0"},
                "want": False,
            },
        ]

        for test_case in test_cases:
            with self.subTest(name=test_case["name"]):
                self.assertTrue(
                    test_case["want"]
                    == within_read_times(test_case["entry"]["reading_time"])
                )

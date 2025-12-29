import unittest
from dataclasses import dataclass
from typing import Tuple

from wallypub.img.color import (
    get_random_color,
    clamp,
    get_hex_value,
    return_complimentary_color,
)


class TestColor(unittest.TestCase):
    def test_get_random_color(self):
        color = get_random_color()
        self.assertIsInstance(color, tuple)
        self.assertEqual(len(color), 3)
        for c in color:
            self.assertGreaterEqual(c, 0)
            self.assertLessEqual(c, 255)

    def test_clamp(self):
        @dataclass
        class TestCase:
            name: str
            input: int
            expected: int

        testcases = [
            TestCase(name="below_min", input=-10, expected=0),
            TestCase(name="at_min", input=0, expected=0),
            TestCase(name="in_range", input=128, expected=128),
            TestCase(name="at_max", input=255, expected=255),
            TestCase(name="above_max", input=300, expected=255),
        ]

        for case in testcases:
            with self.subTest(msg=case.name):
                actual = clamp(case.input)
                self.assertEqual(case.expected, actual)

    def test_get_hex_value(self):
        @dataclass
        class TestCase:
            name: str
            input: Tuple[int, int, int]
            expected: str

        testcases = [
            TestCase(name="black", input=(0, 0, 0), expected="#000000"),
            TestCase(name="white", input=(255, 255, 255), expected="#ffffff"),
            TestCase(name="red", input=(255, 0, 0), expected="#ff0000"),
            TestCase(name="green", input=(0, 255, 0), expected="#00ff00"),
            TestCase(name="blue", input=(0, 0, 255), expected="#0000ff"),
        ]

        for case in testcases:
            with self.subTest(msg=case.name):
                actual = get_hex_value(case.input)
                self.assertEqual(case.expected, actual)

    def test_return_complimentary_color(self):
        @dataclass
        class TestCase:
            name: str
            input: str
            expected: Tuple[int, int, int]

        testcases = [
            TestCase(name="black", input="#000000", expected=(255, 255, 255)),
            TestCase(name="white", input="#ffffff", expected=(0, 0, 0)),
            TestCase(name="red", input="#ff0000", expected=(0, 255, 255)),
            TestCase(name="green", input="#00ff00", expected=(255, 0, 255)),
            TestCase(name="blue", input="#0000ff", expected=(255, 255, 0)),
        ]

        for case in testcases:
            with self.subTest(msg=case.name):
                actual = return_complimentary_color(case.input)
                self.assertEqual(case.expected, actual)


if __name__ == "__main__":
    unittest.main()

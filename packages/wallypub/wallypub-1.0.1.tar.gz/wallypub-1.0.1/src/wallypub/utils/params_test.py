import unittest
from typing import Callable

from wallypub.conf.app import WallabagURLParameters
from wallypub.utils.params import get_params_from_settings


class TestGetParamsFromSettings(unittest.TestCase):
    cases = [
        # recent parameters case
        WallabagURLParameters(),
        # additional parameters case
        WallabagURLParameters(sort="asc", order="", page="", perPage="", detail=""),
    ]


def _make_test(
    params: WallabagURLParameters,
) -> Callable[[TestGetParamsFromSettings], None]:
    def _test(self: TestGetParamsFromSettings) -> None:
        expected_json = params.model_dump(mode="json")
        result = get_params_from_settings(params)
        self.assertEqual(expected_json, result)

    return _test


for idx, case in enumerate(TestGetParamsFromSettings.cases):
    setattr(TestGetParamsFromSettings, f"test_case_{idx}", _make_test(case))

if __name__ == "__main__":
    unittest.main()

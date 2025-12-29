import json
import unittest

from lionweb.serialization import SerializedJsonComparisonUtils

from starlasuspecs.v1.ast_language import ast_language_json


class StarlasuLanguageV1(unittest.TestCase):

    def test_generation_as_expected(self):
        import os

        script_dir = os.path.dirname(__file__)
        file_path = os.path.join(script_dir, "starlasu.language.v1.json")
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        loaded_json = json.loads(content)
        SerializedJsonComparisonUtils.assert_equivalent_lionweb_json(
            loaded_json, ast_language_json()
        )


if __name__ == "__main__":
    unittest.main()

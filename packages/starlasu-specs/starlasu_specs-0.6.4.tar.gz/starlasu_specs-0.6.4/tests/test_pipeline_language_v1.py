import unittest

from starlasuspecs.v1.pipeline_language import pipeline_language


class PipelineLanguageV1(unittest.TestCase):

    def test_concepts_retrieval(self):
        lang = pipeline_language()
        conc = lang.get_concept_by_name("ComponentParameterConfiguration")
        self.assertEqual("ComponentParameterConfiguration", conc.name)


if __name__ == "__main__":
    unittest.main()

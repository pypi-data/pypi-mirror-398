import sys
import unittest
from pathlib import Path

from click.testing import CliRunner
from treqs.main import treqs
from treqs.create_elements import create_elements


class TestCheckElements(unittest.TestCase):
    # <treqs-element id="7820afae220311ecba31f018989356c1" type="unittest">
    # Success case of creating a new requirement with treqs create.
    # <treqs-link type="tests" target="97a8fb92-9613-11ea-bb37-0242ac130002" />
    # <treqs-link type="tests" target="4c4fbfd250a111edbe22c9328ceec9a7" />
    # <treqs-link type="tests" target="4d7ca13c76ae11ebb811cf2f044815f7" />
    # </treqs-element>
    def test_create_element(self):
        ce = create_elements
        return_value = ce.create_markdown_element(
            "userstory", Path(__file__).parent / "../templates", "requrement"
        )

        self.assertIsInstance(return_value, str)

        # Adding a fake <treqs-element type="information" id="testdata1"> so that the parser does not fail.
        self.assertEqual(
            return_value[53:],
            'type="userstory">\n\nrequrement\n\n### As a : TBD\n### I want : TBD\n### so that: TBD\n\n</treqs-element>',
        )

    # <treqs-element id="047edcbc55d311f0924e8adebfb72d7e" type="unittest">
    # Test treqs create in interactive mode via command line interface.
    # <treqs-link type="tests" target="b09debd2509f11edbe22c9328ceec9a7" />
    # </treqs-element>
    def test_create_interactive_mode(self):
        runner = CliRunner()
        result = runner.invoke(
            treqs,
            [
                "create",
                "--interactive",
            ],
            input="\n\n",
        )
        # TODO Make sure that the right questions are asked.
        self.assertTrue(result.exit_code == 0)
        self.assertTrue("userstory" in result.output)
        self.assertEqual(513, len(result.output))

    # <treqs-element id="81caf9d655d211f0bec38adebfb72d7e" type="unittest">
    # Test creating multiple elements via command line interface.
    # <treqs-link type = "tests" target="58a1dcae50ae11edbe22c9328ceec9a7"/>
    # </treqs-element>
    def test_create_multiple_elements(self):
        runner = CliRunner()
        result = runner.invoke(
            treqs,
            [
                "create",
                "--type",
                "userstory",
                "--label",
                "my label",
                "--amount",
                "2",
            ],
        )

        self.assertTrue(result.exit_code == 0)
        # TODO Make sure that two userstories are in the output
        self.assertTrue("userstory" in result.output)
        self.assertEqual(298, len(result.output))

    # <treqs-element id="1edc9f4e512211ed96518adebfb72d7e" type="unittest">
    # Success case of creating a new requirement with treqs create.
    # <treqs-link type="tests" target="39f253a076ae11ebb811cf2f044815f7" />
    # </treqs-element>
    def test_create_template(self):
        ce = create_elements
        return_value = ce.create_markdown_new_template(
            "qualityattribute",
            Path(__file__).parent / "../templates",
            "planguage",
            "requirement",
        )

        self.assertIsInstance(return_value, str)

        # Adding a fake <treqs-element type="information" id="testdata2"> so that the parser does not fail.
        self.assertEqual(
            return_value[53:],
            'type="qualityattribute">\n\nrequirement\n\n### TAG: TBD\n### PLAN: TBD\n### SCALE: TBD\n### MUST: TBD\n### STRETCH: TBD\n### WISH: TBD\n### RECORD: TBD\n### TREND: TBD\n### STAKEHOLDER: TBD\n### AUTHORITY: TBD\n### DEFINED: TBD\n\n</treqs-element>',
        )

    # <treqs-element id="1edc9ecc512211ed96518adebfb72d7e" type="unittest">
    # Success case of creating a new requirement with treqs create.
    # <treqs-link type="tests" target="39f253a076ae11ebb811cf2f044815f7" />
    # </treqs-element>
    def test_notemplate(self):
        ce = create_elements
        return_value = ce.create_markdown_element(
            "goal", Path(__file__).parent / "../templates", "requrement"
        )
        self.assertIsInstance(return_value, str)
        self.assertEqual(return_value, "No matching template found")
        # Let's try the other method as well...
        return_value = ce.create_markdown_new_template(
            "goal",
            Path(__file__).parent / "../templates",
            "istar",
            "requrement",
        )
        self.assertIsInstance(return_value, str)
        self.assertEqual(return_value, "No matching template found")

    # <treqs-element id="7820af68220311ecba31f018989356c1" type="unittest">
    # Success case of creating a new link with treqs createlink.
    # <treqs-link type="tests" target="9cec8bee512011ed8f118adebfb72d7e" />
    # </treqs-element>
    def test_create_link(self):
        ce = create_elements
        return_value = ce.create_link("relatesTo", "6666")

        self.assertIsInstance(return_value, str)
        self.assertEqual(
            return_value, '<treqs-link type="relatesTo" target="6666" />'
        )

    # <treqs-element id="7820ae78220311ecba31f018989356c1" type="unittest">
    # Success case of generating an id with treqs generateid.
    # <treqs-link type="tests" target="274368b8220011ecb90df018989356c1" />
    # </treqs-element>
    def test_generateid(self):
        ce = create_elements
        return_value = ce.generate_id(1)

        self.assertIsInstance(return_value, str)
        self.assertEqual(len(return_value), 33)

    # <treqs-element id="7c8d8bf8512211ed949e8adebfb72d7e" type="unittest">
    # Success case of generating an id with treqs generateid.
    # <treqs-link type="tests" target="274368b8220011ecb90df018989356c1" />
    # </treqs-element>
    def test_generateid_negative_integer(self):
        ce = create_elements
        return_value = ce.generate_id(-342)

        self.assertIsInstance(return_value, str)
        self.assertEqual(return_value, "Amount has to be a positive integer.")

    # <treqs-element id="7c8d8c66512211ed949e8adebfb72d7e" type="unittest">
    # Success case of generating an id with treqs generateid.
    # <treqs-link type="tests" target="274368b8220011ecb90df018989356c1" />
    # <treqs-link type="tests" target="3fe7839e509f11edbe22c9328ceec9a7" />
    # </treqs-element>
    def test_generateid_many(self):
        ce = create_elements
        return_value = ce.generate_id(2)

        self.assertIsInstance(return_value, str)
        self.assertEqual(len(return_value), 66)

    # <treqs-element id="7c8d8c7a512211ed949e8adebfb72d7e" type="unittest">
    # Success case of generating an id with treqs generateid.
    # <treqs-link type="tests" target="274368b8220011ecb90df018989356c1" />
    # </treqs-element>
    def test_generateid_string(self):
        ce = create_elements
        return_value = ce.generate_id("test string")

        self.assertIsInstance(return_value, str)
        self.assertEqual(return_value, "Amount cannot be a string.")

    # <treqs-element id="7c8d8c8e512211ed949e8adebfb72d7e" type="unittest">
    # Success case of generating an id with treqs generateid.
    # <treqs-link type="tests" target="274368b8220011ecb90df018989356c1" />
    # </treqs-element>
    def test_generateid_zero(self):
        ce = create_elements
        return_value = ce.generate_id(0)
        self.assertEqual(return_value, "Amount has to be a positive integer.")

    # <treqs-element id="7c8d8ca2512211ed949e8adebfb72d7e" type="unittest">
    # Success case of generating an id with treqs generateid.
    # <treqs-link type="tests" target="274368b8220011ecb90df018989356c1" />
    # </treqs-element>
    def test_generateid_max(self):
        ce = create_elements
        return_value = ce.generate_id(sys.maxsize)
        self.assertIsInstance(return_value, str)
        self.assertEqual(return_value, "Amount cannot be larger 100.")

    # <treqs-element id="7c8d8cac512211ed949e8adebfb72d7e" type="unittest">
    # Success case of generating an id with treqs generateid.
    # <treqs-link type="tests" target="274368b8220011ecb90df018989356c1" />
    # </treqs-element>
    def test_generateid_min(self):
        ce = create_elements
        return_value = ce.generate_id(-1 * sys.maxsize)
        self.assertEqual(return_value, "Amount has to be a positive integer.")


if __name__ == "__main__":
    unittest.main()

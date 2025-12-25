import unittest
from click.testing import CliRunner
from treqs.main import treqs


class TestClickCreate(unittest.TestCase):
    # <treqs-element id="5b7383e44fc611edaf3593e6ba6c979b" type="unittest">
    # Test whether the UI is by default in non interactive mode.
    # <treqs-link type="tests" target="39f253a076ae11ebb811cf2f044815f7" />
    # <treqs-link type="tests" target="4d7ca13c76ae11ebb811cf2f044815f7" />
    # <treqs-link type="tests" target="4c4fbfd250a111edbe22c9328ceec9a7" />
    # </treqs-element>
    def test_treqs_create_non_interactive(self):
        runner = CliRunner()
        result = runner.invoke(treqs, ["create"])
        assert result.exit_code == 0
        assert (
            'type="undefined">\n\n\n\n### Treqs element\n\n<!-- Use markdown to describe the treqs element. Consider to \n     use ears template for system requirements, userstory \n     template for user stories, or planguage template for \n     quality requirements. -->\n\n'
            in result.output
        )

    # <treqs-element id="994662404fc611edaf3593e6ba6c979b" type="unittest">
    # Test treqs create defaults to the default template for unknown types.
    # <treqs-link type="tests" target="39f253a076ae11ebb811cf2f044815f7" />
    # <treqs-link type="tests" target="4d7ca13c76ae11ebb811cf2f044815f7" />
    # <treqs-link type="tests" target="4c4fbfd250a111edbe22c9328ceec9a7" />
    # </treqs-element>
    def test_treqs_create_unknown_type(self):
        runner = CliRunner()
        result = runner.invoke(
            treqs, ["create", "--interactive"], input="cluster-of-concern\n\n"
        )
        assert result.exit_code == 0
        assert (
            'type="cluster-of-concern">\n\n\n\n### Treqs element\n\n<!-- Use markdown to describe the treqs element. Consider to \n     use ears template for system requirements, userstory \n     template for user stories, or planguage template for \n     quality requirements. -->\n\n'
            in result.output
        )
        assert (
            "Template not found for this type. Output generated with default template. Refer to treqs create --help."
            in result.output
        )


if __name__ == "__main__":
    unittest.main()

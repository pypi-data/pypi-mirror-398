import importlib
import unittest
from click.testing import CliRunner
from treqs import __package_name__
from treqs.main import treqs


class TestCLI(unittest.TestCase):
    # <treqs-element id="9bde2919fff711efac6ad89ef374263e" type="unittest">
    # Tests whether cli allows to print the treqs version.
    # <treqs-link type="tests" target="54dbfbe5fff711efba90d89ef374263e"/>
    # </treqs-element>
    def test_treqs_cli_version(self):
        runner = CliRunner()
        result = runner.invoke(treqs, ["--version"])
        version = importlib.metadata.version(__package_name__)
        assert result.exit_code == 0
        assert version in result.output

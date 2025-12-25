import io
import os
import random
import sys
import time
import unittest
from unittest import mock

from click.testing import CliRunner

from treqs.main import treqs
from tests.performance_setup import generate_performance_test_data

PERFORMANCE_TEST_DATA_DIR = "test_data/performance"
SHREQ_COUNT = 625
SYSREQ_COUNT = 1875
TEST_COUNT = 2500
MAX_ALLOWED_TIME = 10  # seconds


class TestPerformance(unittest.TestCase):
    def setUp(self):
        generate_performance_test_data(
            test_dir=PERFORMANCE_TEST_DATA_DIR,
            SHReq_count=SHREQ_COUNT,
            SysReq_count=SYSREQ_COUNT,
            Test_count=TEST_COUNT,
        )

    def tearDown(self):
        if os.path.exists(PERFORMANCE_TEST_DATA_DIR + os.sep + "shreqs.md"):
            os.remove(PERFORMANCE_TEST_DATA_DIR + os.sep + "shreqs.md")
        if os.path.exists(PERFORMANCE_TEST_DATA_DIR + os.sep + "sysreqs.md"):
            os.remove(PERFORMANCE_TEST_DATA_DIR + os.sep + "sysreqs.md")
        if os.path.exists(PERFORMANCE_TEST_DATA_DIR + os.sep + "tests.md"):
            os.remove(PERFORMANCE_TEST_DATA_DIR + os.sep + "tests.md")

    def _get_time(self, command, *args):
        import logging

        # Save original stdout and stderr
        orig_stdout = sys.stdout
        orig_stderr = sys.stderr
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()

        # Patch logging to suppress all logs
        with mock.patch("logging.Logger._log"):
            try:
                start = time.perf_counter()
                runner = CliRunner()
                runner.invoke(
                    treqs,
                    [command, PERFORMANCE_TEST_DATA_DIR] + list(args),
                )
                end = time.perf_counter()
            finally:
                # Restore stdout and stderr
                sys.stdout = orig_stdout
                sys.stderr = orig_stderr
        return end - start

    # <treqs-element id="b09cd1bb559211f0a3a0e0d55e880b93" type="unittest">
    # <treqs-link target="549fa3fa559211f0b3b7e0d55e880b93" type="tests" />
    # </treqs-element>
    def test_list_inlinks_and_outlinks_performance(self):
        time_taken = self._get_time("list", "--outlinks", "--inlinks")
        self.assertLessEqual(
            time_taken,
            MAX_ALLOWED_TIME,
            f"Command took too long: {time_taken:.2f} seconds",
        )

    # <treqs-element id="087fbd12559311f0a938e0d55e880b93" type="unittest">
    # <treqs-link target="549fa3fa559211f0b3b7e0d55e880b93" type="tests" />
    # </treqs-element>
    def test_list_elements_performance(self):
        time_taken = self._get_time("list")
        self.assertLessEqual(
            time_taken,
            MAX_ALLOWED_TIME,
            f"Command took too long: {time_taken:.2f} seconds",
        )

    # <treqs-element id="1c6f1c7d559311f0a0f3e0d55e880b93" type="unittest">
    # <treqs-link target="549fa3fa559211f0b3b7e0d55e880b93" type="tests" />
    # </treqs-element>
    def test_check_performance(self):
        time_taken = self._get_time("check")
        self.assertLessEqual(
            time_taken,
            MAX_ALLOWED_TIME,
            f"Command took too long: {time_taken:.2f} seconds",
        )

    # <treqs-element id="15168cde559311f0ae70e0d55e880b93" type="unittest">
    # <treqs-link target="549fa3fa559211f0b3b7e0d55e880b93" type="tests" />
    # </treqs-element>
    def test_list_inlinks_and_outlinks_with_plantuml_performance(self):
        time_taken = self._get_time(
            "list", "--outlinks", "--inlinks", "--plantuml"
        )
        self.assertLessEqual(
            time_taken,
            MAX_ALLOWED_TIME,
            f"Command took too long: {time_taken:.2f} seconds",
        )


if __name__ == "__main__":
    unittest.main()

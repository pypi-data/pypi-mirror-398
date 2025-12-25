import logging
import unittest
from pathlib import Path
from unittest.mock import patch

from treqs.file_traverser import file_traverser

# Constants
RECURSIVE_BASE_DIR = Path("tests/test-ignored-files")
FAILING_HANDLER_RECURSIVE_FILE = str(RECURSIVE_BASE_DIR)
FAILING_HANDLER_NON_RECURSIVE_FILE = str(RECURSIVE_BASE_DIR)
IGNORED_FILE = str(RECURSIVE_BASE_DIR / "ignored-file.md")
IGNORED_SUBDIR = str(RECURSIVE_BASE_DIR / "ignored_subdir")
NON_IGNORED_FILE = str(RECURSIVE_BASE_DIR / "non-ignored-file.md")

NON_EXISTING_FILE_TRAVERSER_FILE = str(Path("./tests/test_data/6-link.md"))
ROBUSTNESS_ON_PARSER_ERRORS_FILE = str(
    Path("./tests/test_data/binary_file.png")
)
EXISTING_FILE_TRAVERSER_FILE = str(
    Path("./tests/test_data/5-test-faulty-types-and-links.md")
)
GENERIC_TRAVERSER_STRATEGY_FILE = str(
    Path("./tests/test_data/5-test-faulty-types-and-links.md")
)

NON_RECURSIVE_BASE_DIR = Path("tests/test_data/test-recursive-traverser")
NON_RECURSIVE_FILE_TRAVERSER_FILE = str(NON_RECURSIVE_BASE_DIR)
EMPTY_DIR_FILE = str(NON_RECURSIVE_BASE_DIR / "6-test-empty-dir")
TEST_TREQ_FILE_1 = str(NON_RECURSIVE_BASE_DIR / "test-treq-file-1.md")
TEST_TREQ_FILE_2 = str(NON_RECURSIVE_BASE_DIR / "test-treq-file-2.md")
TEST_TREQ_FILE_3 = str(NON_RECURSIVE_BASE_DIR / "test-treq-file-3.py")

NON_XML_MD_FILES = str(Path("./tests/test_data/6-test-traverse-treqs.md"))
NON_XML_PY_FILES = str(Path("./tests/test_data/6-test-traverse-treqs.py"))
NON_EXISTING_NON_RECURSIVE_FILE_TRAVERSER = str(
    Path("./tests/test_data/6-link")
)

TREQS_IGNORE_BASE_DIR = Path("tests/test-ignored-files")
TREQS_IGNORE_FILE = str(TREQS_IGNORE_BASE_DIR)
TREQS_IGNORED_FILE = str(TREQS_IGNORE_BASE_DIR / "ignored-file.md")
TREQS_NON_IGNORED_FILE = str(TREQS_IGNORE_BASE_DIR / "non-ignored-file.md")
TREQS_IGNORED_FILE_BY_NESTED_TREQS_IGNORE = str(
    TREQS_IGNORE_BASE_DIR / "ignore-me.md"
)
TREQS_NON_IGNORED_NESTED_FILE = str(
    TREQS_IGNORE_BASE_DIR / "ignore-me" / "this-is-not-ignored.py"
)
XML_TRAVERSAL_WITHOUT_SELECTOR_FILE = str(
    Path("tests/test_data/6-test-traverse-treqs-without_selector.md")
)
XML_TRAVERSAL_WITH_PARSER_ERROR_FILE = str(
    Path("tests/test_data/6-test-traverse-treqs-with_parser_error.md")
)
XML_TRAVERSAL_IGNORE_PLANTUML_BLOCK_FILE = str(
    Path("tests/test_data/real-world-samples/sensit-requirements-draft.md")
)
XML_TRAVERSAL_WITH_LANGUAGES_FILE = str(
    Path("tests/test_data/real-world-samples/java_with_generic_code.java")
)
REALISTIC_PLANTUML_EXAMPLE = str(
    Path("tests/test_data/real-world-samples/plantuml-model.md")
)

SYMLINKS_BASE_DIR = Path("tests/test_data/symlinks")
CIRCULAR_SYMLINKS_BASE_DIR = Path("tests/test_data/circular-symlinks")


class TestFileTraverser(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger("treqs-on-git.treqs-ng")

    # handler that prints the type and id of each element, then just returns successfully
    def print_handler_function(self, file_name, element=""):
        if element != "":
            self.logger.info(
                "   | %s | %s |", element.get("type"), element.get("id")
            )
        return 0

    # handler that prints the tag of each element, then just returns successfully
    def print_tag_handler_function(self, file_name, element=""):
        if element != "":
            self.logger.info(element.tag)
        return 0

    # handler that just returns successfully
    def silent_handler_function(self, file_name, element=""):
        return 0

    # handler that just returns unsuccessfully
    def failing_handler_function(self, file_name, element=""):
        return 1

    # <treqs-element id="d210a606559c11f0b50c8adebfb72d7e" type="unittest">
    # Test whether treqs-elements can be read in a markdown file
    # <treqs-link type="tests" target="51928136509311edbe22c9328ceec9a7"/>
    # <treqs-link type="tests" target="571a0556509411edbe22c9328ceec9a7"/>
    # <treqs-link type="tests" target="48f619d6dfae11ef97f0d89ef374263e"/>
    # <treqs-link type="tests" target="5fc95868a72d11efa3728adebfb72d7c"/>
    # </treqs-element>
    def test_existing_file_traverser(self):
        with self.assertLogs("treqs-on-git.treqs-ng", level=10) as captured:
            f_traverse = file_traverser()
            success = f_traverse.traverse_file_hierarchy(
                EXISTING_FILE_TRAVERSER_FILE,
                True,
                self.print_handler_function,
                f_traverse.traverse_XML_file,
                ".//treqs-element",
            )

            self.assertEqual(success, 0)

        self.assertEqual(len(captured.records), 14)
        self.assertEqual(
            captured.records[0].getMessage(), "file_traverser created"
        )
        self.assertEqual(
            captured.records[1].getMessage(),
            f"\n\nCalling XML traversal with filename {EXISTING_FILE_TRAVERSER_FILE}",
        )
        self.assertEqual(
            captured.records[2].getMessage(),
            f"   ### Processing elements in File {EXISTING_FILE_TRAVERSER_FILE}",
        )
        self.assertEqual(
            captured.records[3].getMessage(),
            "   | non-existing-type | e770de36920911eb9355f018989356c1 |",
        )
        self.assertEqual(
            captured.records[4].getMessage(),
            "   | requirement | 2c600896920a11ebbb6ff018989356c1 |",
        )
        self.assertEqual(
            captured.records[5].getMessage(),
            "   | requirement | 56cbd2e0920a11ebb9d1f018989356c1 |",
        )
        self.assertEqual(
            captured.records[6].getMessage(), "   | information | None |"
        )
        self.assertEqual(
            captured.records[7].getMessage(),
            "   | requirement | 940f4d62920a11eba034f018989356c1 |",
        )
        self.assertEqual(
            captured.records[8].getMessage(),
            "   | requirement | 940f4d62920a11eba034f018989356c1 |",
        )
        self.assertEqual(
            captured.records[9].getMessage(),
            "   | requirement | c5402c1a919411eb8311f018989356c1 |",
        )
        self.assertEqual(
            captured.records[10].getMessage(),
            "   | requirement | 4f5bcadad45711eb9de4f018989356c1 |",
        )
        self.assertEqual(
            captured.records[11].getMessage(),
            "   | requirement | 3cabd686d45811ebaaeef018989356c1 |",
        )
        self.assertEqual(
            captured.records[12].getMessage(),
            "   |  | 9d3a98c80bd711ec8e3ff018989356c1 |",
        )
        self.assertEqual(
            captured.records[13].getMessage(),
            "   | unittest | dummy_test |",
        )
        # It seems like we are using return codes inconsistently. In this file, 0 is success. In filetraverser, it looks like 1 is success.
        self.assertEqual(0, f_traverse.filecount)

    def test_generic_traverser_strategy(self):
        with self.assertLogs("treqs-on-git.treqs-ng", level=10) as captured:
            f_traverse = file_traverser()
            success = f_traverse.traverse_file_hierarchy(
                GENERIC_TRAVERSER_STRATEGY_FILE,
                True,
                self.silent_handler_function,
            )

            self.assertEqual(success, 0)

        self.assertEqual(len(captured.records), 3)
        self.assertEqual(
            captured.records[0].getMessage(), "file_traverser created"
        )
        self.assertEqual(
            captured.records[1].getMessage(),
            "Choosing generic traversal strategy",
        )
        self.assertEqual(
            captured.records[2].getMessage(),
            f"   ### Processing elements in File {GENERIC_TRAVERSER_STRATEGY_FILE}",
        )

    # <treqs-element id="9f82554c559f11f0a27b8adebfb72d7e" type="unittest">
    # Test whether file traverser is robust against parser errors.
    # <treqs-link target="4d8be51c-df13-41e9-ac02-00ffa31c3b80" type="tests"/>
    # </treqs-element>
    def test_robustness_on_parser_errors(self):
        """Tests that no exception occurs when processing binary files."""
        with self.assertLogs("treqs-on-git.treqs-ng", level=10) as captured:
            f_traverse = file_traverser()
            success = f_traverse.traverse_file_hierarchy(
                ROBUSTNESS_ON_PARSER_ERRORS_FILE,
                True,
                self.silent_handler_function,
                f_traverse.traverse_XML_file,
            )

            self.assertEqual(success, 0)
            self.assertEqual(len(captured.records), 4)
            self.assertEqual(
                captured.records[0].getMessage(), "file_traverser created"
            )
            self.assertEqual(
                captured.records[1].getMessage(),
                f"\n\nCalling XML traversal with filename {ROBUSTNESS_ON_PARSER_ERRORS_FILE}",
            )
            self.assertEqual(
                captured.records[2].getMessage(),
                f"   ### Processing elements in File {ROBUSTNESS_ON_PARSER_ERRORS_FILE}",
            )
            self.assertEqual(
                captured.records[3].getMessage(),
                f"   ### Skipping elements in File {ROBUSTNESS_ON_PARSER_ERRORS_FILE} due to UnicodeDecodeError",
            )

    def test_failing_handler_recursive(self):
        """Tests that the handler success variable is reached through to the traversal return value, and that no exception occurs."""
        with self.assertLogs("treqs-on-git.treqs-ng", level=10) as captured:
            f_traverse = file_traverser()
            success = f_traverse.traverse_file_hierarchy(
                FAILING_HANDLER_RECURSIVE_FILE,
                True,
                self.failing_handler_function,
            )

            self.assertEqual(success, 1)
            self.assertEqual(len(captured.records), 9)

            records = [r.getMessage() for r in captured.records]
            self.assertIn("file_traverser created", records)
            self.assertIn("Choosing generic traversal strategy", records)
            self.assertIn(
                f"   ### Ignoring file {IGNORED_FILE} (.treqs-ignore)", records
            )
            self.assertIn(
                f"   ### Processing elements in File {NON_IGNORED_FILE}",
                records,
            )

    # <treqs-element id="b3c0f8d4-2e1a-11eb-adc1-0242ac130043" type="unittest">
    # Tests that circular symlinks are handled gracefully.
    # <treqs-link type="tests" target="4869375b51f211f0b3c0e0d55e880b93" />
    # </treqs-element>
    def test_circular_symlinks(self):
        """Tests that ciruclar symlinks are processed correctly."""
        with self.assertLogs("treqs-on-git.treqs-ng", level=10) as captured:
            f_traverse = file_traverser(ignore_root=CIRCULAR_SYMLINKS_BASE_DIR)
            success = f_traverse.traverse_file_hierarchy(
                CIRCULAR_SYMLINKS_BASE_DIR,
                True,
                self.print_handler_function,
                f_traverse.traverse_generic_file,
                ".//treqs-element",
            )

            self.assertEqual(success, 0)

        want_records = [
            "file_traverser created",
            "   ### Processing elements in File tests/test_data/circular-symlinks/real-world-samples/java_with_generic_code.java",
            "   ### Processing elements in File tests/test_data/circular-symlinks/real-world-samples/sensit-requirements-draft.md",
            "   ### Processing elements in File tests/test_data/circular-symlinks/real-world-samples/README.md",
        ]

        captured_records = [r.getMessage() for r in captured.records]
        for record in want_records:
            self.assertIn(record, captured_records)

    # <treqs-element id="b3c0f8d4-2e1a-11eb-adc1-0242ac130003" type="unittest">
    # Tests that symlinks are followed and processed correctly.
    # <treqs-link type="tests" target="f2e3b7e0a80011efb7a7d89ef374263e" />
    # </treqs-element>
    def test_symlinks(self):
        """Tests that symlinks are followed and processed correctly."""
        with self.assertLogs("treqs-on-git.treqs-ng", level=10) as captured:
            f_traverse = file_traverser(ignore_root=SYMLINKS_BASE_DIR)
            success = f_traverse.traverse_file_hierarchy(
                SYMLINKS_BASE_DIR,
                True,
                self.print_handler_function,
                f_traverse.traverse_generic_file,
                ".//treqs-element",
            )

            self.assertEqual(success, 0)

        want_records = [
            "file_traverser created",
            "   ### Processing elements in File tests/test_data/symlinks/real-world-samples/java_with_generic_code.java",
            "   ### Processing elements in File tests/test_data/symlinks/real-world-samples/sensit-requirements-draft.md",
            "   ### Processing elements in File tests/test_data/symlinks/real-world-samples/README.md",
        ]
        captured_records = [r.getMessage() for r in captured.records]
        for record in want_records:
            self.assertIn(record, captured_records)

    def test_failing_handler_non_recursive(self):
        """Tests that the handler success variable is reached through to the traversal return value, and that no exception occurs."""
        with self.assertLogs("treqs-on-git.treqs-ng", level=10) as captured:
            f_traverse = file_traverser()
            success = f_traverse.traverse_file_hierarchy(
                FAILING_HANDLER_NON_RECURSIVE_FILE,
                False,
                self.failing_handler_function,
            )

            self.assertEqual(success, 1)
            self.assertEqual(len(captured.records), 8)

            # Get all logged messages
            records = [r.getMessage() for r in captured.records]

            # Check expected messages are present
            self.assertIn("file_traverser created", records)
            self.assertIn("Choosing generic traversal strategy", records)
            self.assertIn(
                f"   ### Ignoring file {IGNORED_FILE} (.treqs-ignore)", records
            )
            self.assertIn(
                f"\n\n### Non-recursive file_traverser, skipping directory {IGNORED_SUBDIR}",
                records,
            )
            self.assertIn(
                f"   ### Processing elements in File {NON_IGNORED_FILE}",
                records,
            )

    def test_non_existing_file_traverser(self):
        with self.assertLogs("treqs-on-git.treqs-ng", level=10) as captured:
            f_traverse = file_traverser()
            success = f_traverse.traverse_file_hierarchy(
                NON_EXISTING_FILE_TRAVERSER_FILE,
                True,
                self.silent_handler_function,
                f_traverse.traverse_XML_file,
                ".//treqs-element",
            )

        self.assertEqual(success, 1)

        self.assertEqual(len(captured.records), 2)
        self.assertEqual(
            captured.records[0].getMessage(), "file_traverser created"
        )
        self.assertEqual(
            captured.records[1].getMessage(),
            f"\n\n### File or directory {NON_EXISTING_FILE_TRAVERSER_FILE} does not exist. Skipping.",
        )

    # <treqs-element id="89058140559f11f0b73c8adebfb72d7e" type="unittest">
    # Tests non-recursive parsing of all files in a folder.
    # <treqs-link type="tests" target="a40a5ce0dfb011efbe55d89ef374263e"/>
    # </treqs-element>
    def test_non_recursive_file_traverser(self):
        with self.assertLogs("treqs-on-git.treqs-ng", level=10) as captured:
            f_traverse = file_traverser()
            success = f_traverse.traverse_file_hierarchy(
                NON_RECURSIVE_FILE_TRAVERSER_FILE,
                False,
                self.silent_handler_function,
                f_traverse.traverse_XML_file,
                ".//treqs-element",
            )

            self.assertEqual(success, 0)
        self.assertEqual(len(captured.records), 8)
        self.assertEqual(
            captured.records[0].getMessage(), "file_traverser created"
        )
        self.assertEqual(
            captured.records[1].getMessage(),
            f"\n\n### Non-recursive file_traverser, skipping directory {EMPTY_DIR_FILE}",
        )
        self.assertEqual(
            captured.records[2].getMessage(),
            f"\n\nCalling XML traversal with filename {TEST_TREQ_FILE_1}",
        )
        self.assertEqual(
            captured.records[3].getMessage(),
            f"   ### Processing elements in File {TEST_TREQ_FILE_1}",
        )
        self.assertEqual(
            captured.records[4].getMessage(),
            f"\n\nCalling XML traversal with filename {TEST_TREQ_FILE_2}",
        )
        self.assertEqual(
            captured.records[5].getMessage(),
            f"   ### Processing elements in File {TEST_TREQ_FILE_2}",
        )
        self.assertEqual(
            captured.records[6].getMessage(),
            f"\n\nCalling XML traversal with filename {TEST_TREQ_FILE_3}",
        )
        self.assertEqual(
            captured.records[7].getMessage(),
            f"   ### Processing elements in File {TEST_TREQ_FILE_3}",
        )

    # <treqs-element id="0316421cc79211eba976f018989356c1" type="unittest">
    # Tests that non-XML MD files work, and that nested treqs-elements are found
    # <treqs-link type="tests" target="bc89e02a76c811ebb811cf2f044815f7" />
    # <treqs-link type="tests" target="638fa22e76c911ebb811cf2f044815f7" />
    # </treqs-element>
    def test_non_xml_md_files(self):
        with self.assertLogs("treqs-on-git.treqs-ng", level=10) as captured:
            f_traverse = file_traverser()
            success = f_traverse.traverse_file_hierarchy(
                NON_XML_MD_FILES,
                False,
                self.print_handler_function,
                f_traverse.traverse_XML_file,
                ".//treqs-element",
            )

            self.assertEqual(success, 0)

        self.assertEqual(len(captured.records), 6)
        self.assertEqual(
            captured.records[0].getMessage(), "file_traverser created"
        )

        self.assertEqual(
            captured.records[1].getMessage(),
            f"\n\nCalling XML traversal with filename {NON_XML_MD_FILES}",
        )
        self.assertEqual(
            captured.records[2].getMessage(),
            f"   ### Processing elements in File {NON_XML_MD_FILES}",
        )
        self.assertEqual(
            captured.records[3].getMessage(),
            "   | requirement | 0276e84ac79011ebb719f018989356c1 |",
        )
        self.assertEqual(
            captured.records[4].getMessage(),
            "   | requirement | ff403b04c78f11ebbdc9f018989356c1 |",
        )
        self.assertEqual(
            captured.records[5].getMessage(),
            "   | requirement | c5ae0c10c79211eb9631f018989356c1 |",
        )

    # <treqs-element id="330c1b6cc79311eba583f018989356c1" type="unittest">
    # Tests that non-XML non-MD (py) files work
    # <treqs-link type="tests" target="46422be0e2d311efb5048adebfb72d7c" />
    # <treqs-link type="tests" target="a0820e06-9614-11ea-bb37-0242ac130002" />
    # </treqs-element>
    def test_non_xml_py_files(self):
        with self.assertLogs("treqs-on-git.treqs-ng", level=10) as captured:
            f_traverse = file_traverser()
            success = f_traverse.traverse_file_hierarchy(
                NON_XML_PY_FILES,
                False,
                self.print_handler_function,
                f_traverse.traverse_XML_file,
                ".//treqs-element",
            )

            self.assertEqual(success, 0)

        self.assertEqual(len(captured.records), 4)
        self.assertEqual(
            captured.records[0].getMessage(), "file_traverser created"
        )

        self.assertEqual(
            captured.records[1].getMessage(),
            f"\n\nCalling XML traversal with filename {NON_XML_PY_FILES}",
        )
        self.assertEqual(
            captured.records[2].getMessage(),
            f"   ### Processing elements in File {NON_XML_PY_FILES}",
        )
        self.assertEqual(
            captured.records[3].getMessage(),
            "   | unittest | 9c0adc12c79211ebb9cbf018989356c1 |",
        )

    def test_non_existing_non_recursive_file_traverser(self):
        with self.assertLogs("treqs-on-git.treqs-ng", level=10) as captured:
            f_traverse = file_traverser()
            success = f_traverse.traverse_file_hierarchy(
                NON_EXISTING_NON_RECURSIVE_FILE_TRAVERSER,
                False,
                self.print_handler_function,
                f_traverse.traverse_XML_file,
                ".//treqs-element",
            )

            self.assertEqual(success, 1)

        self.assertEqual(len(captured.records), 2)
        self.assertEqual(
            captured.records[0].getMessage(), "file_traverser created"
        )
        self.assertEqual(
            captured.records[1].getMessage(),
            f"\n\n### File or directory {NON_EXISTING_NON_RECURSIVE_FILE_TRAVERSER} does not exist. Skipping.",
        )

    # <treqs-element id="721192f255a011f09f7a8adebfb72d7e" type="unittest">
    # Tests whether files can be excluded via treqs-ignore
    # <treqs-link type="tests" target="4b2829b6dfb111ef9c8dd89ef374263e"/>
    # </treqs-element>
    def test_treqs_ignore(self):
        with self.assertLogs("treqs-on-git.treqs-ng", level=10) as captured:
            f_traverse = file_traverser()
            success = f_traverse.traverse_file_hierarchy(
                TREQS_IGNORE_FILE,
                True,
                self.print_handler_function,
                f_traverse.traverse_XML_file,
                ".//treqs-element",
            )

            self.assertEqual(success, 0)

        self.assertEqual(len(captured.records), 11)
        self.assertEqual(
            captured.records[0].getMessage(), "file_traverser created"
        )

        records = [r.getMessage() for r in captured.records]
        self.assertIn(
            f"   ### Ignoring file {TREQS_IGNORED_FILE} (.treqs-ignore)",
            records,
        )
        self.assertIn(
            f"\n\nCalling XML traversal with filename {TREQS_NON_IGNORED_FILE}",
            records,
        )
        self.assertIn(
            f"   ### Processing elements in File {TREQS_NON_IGNORED_FILE}",
            records,
        )

    # <treqs-element id="a086948a3e6545b5b88f697a97d691f7" type="unittest">
    # Tests that nested .treqs-ignore files are ignored
    # <treqs-link type="tests" target="8552d169baa44b4eb9afd875f80bdac0" />
    # </treqs-element>
    def test_nested_treqs_ignore(self):
        with self.assertLogs("treqs-on-git.treqs-ng", level=10) as captured:
            f_traverse = file_traverser()
            success = f_traverse.traverse_file_hierarchy(
                TREQS_IGNORE_FILE,
                True,
                self.print_handler_function,
                f_traverse.traverse_XML_file,
                ".//treqs-element",
            )

            self.assertEqual(success, 0)

        self.assertEqual(len(captured.records), 11)
        self.assertEqual(
            captured.records[0].getMessage(), "file_traverser created"
        )

        records = [r.getMessage() for r in captured.records]
        self.assertIn(
            f"   ### Ignoring file {TREQS_IGNORED_FILE} (.treqs-ignore)",
            records,
        )
        self.assertIn(
            f"   ### Ignoring file {TREQS_IGNORED_FILE_BY_NESTED_TREQS_IGNORE} (.treqs-ignore)",
            records,
        )
        self.assertIn(
            f"   ### Processing elements in File {TREQS_NON_IGNORED_FILE}",
            records,
        )
        self.assertIn(
            f"   ### Processing elements in File {TREQS_NON_IGNORED_NESTED_FILE}",
            records,
        )

    def test_XML_traversal_without_selector(self):
        with self.assertLogs("treqs-on-git.treqs-ng", level=10) as captured:
            f_traverse = file_traverser()
            success = f_traverse.traverse_file_hierarchy(
                XML_TRAVERSAL_WITHOUT_SELECTOR_FILE,
                False,
                self.print_tag_handler_function,
                f_traverse.traverse_XML_file,
            )

            self.assertEqual(success, 0)

        self.assertEqual(len(captured.records), 5)
        self.assertEqual(
            captured.records[0].getMessage(), "file_traverser created"
        )
        self.assertEqual(
            captured.records[1].getMessage(),
            f"\n\nCalling XML traversal with filename {XML_TRAVERSAL_WITHOUT_SELECTOR_FILE}",
        )
        self.assertEqual(
            captured.records[2].getMessage(),
            f"   ### Processing elements in File {XML_TRAVERSAL_WITHOUT_SELECTOR_FILE}",
        )
        self.assertEqual(captured.records[3].getMessage(), "treqs-element")
        self.assertEqual(captured.records[4].getMessage(), "treqs-element")

    def test_XML_traversal_with_parser_error(self):
        with self.assertLogs("treqs-on-git.treqs-ng", level=10) as captured:
            f_traverse = file_traverser()
            success = f_traverse.traverse_file_hierarchy(
                XML_TRAVERSAL_WITH_PARSER_ERROR_FILE,
                False,
                self.print_tag_handler_function,
                f_traverse.traverse_XML_file,
            )

            self.assertEqual(success, 0)

        self.assertEqual(len(captured.records), 4)
        self.assertEqual(
            captured.records[0].getMessage(), "file_traverser created"
        )
        self.assertEqual(
            captured.records[1].getMessage(),
            f"\n\nCalling XML traversal with filename {XML_TRAVERSAL_WITH_PARSER_ERROR_FILE}",
        )
        self.assertEqual(
            captured.records[2].getMessage(),
            f"   ### Processing elements in File {XML_TRAVERSAL_WITH_PARSER_ERROR_FILE}",
        )
        self.assertEqual(
            captured.records[3].getMessage(),
            f"   ### Skipping elements in File {XML_TRAVERSAL_WITH_PARSER_ERROR_FILE} due to parser error ((\"expected '>', line 8, column 1\",))",
        )

    def test_XML_traversal_ignore_plantuml_block(self):
        with self.assertLogs("treqs-on-git.treqs-ng", level=10) as captured:
            f_traverse = file_traverser()
            success = f_traverse.traverse_file_hierarchy(
                XML_TRAVERSAL_IGNORE_PLANTUML_BLOCK_FILE,
                False,
                self.silent_handler_function,
                f_traverse.traverse_XML_file,
                ".//treqs-element",
            )

            self.assertEqual(success, 0)

        self.assertEqual(len(captured.records), 3)
        self.assertEqual(
            captured.records[0].getMessage(), "file_traverser created"
        )
        self.assertEqual(
            captured.records[1].getMessage(),
            f"\n\nCalling XML traversal with filename {XML_TRAVERSAL_IGNORE_PLANTUML_BLOCK_FILE}",
        )
        self.assertEqual(
            captured.records[2].getMessage(),
            f"   ### Processing elements in File {XML_TRAVERSAL_IGNORE_PLANTUML_BLOCK_FILE}",
        )

    # <treqs-element id="5e95a93ea71511efb103d89ef374263e" type="unittest">
    # Test XML file traversal in files with language syntax that uses XML opening and closing tags.
    # <treqs-link type="tests" target="ab59f9c4a71111efaf2ed89ef374263e" />
    # </treqs-element>
    def test_XML_traversal_in_files_with_languages_that_use_xml_tags_openings(
        self,
    ):
        with self.assertLogs("treqs-on-git.treqs-ng", level=10) as captured:
            f_traverse = file_traverser()
            success = f_traverse.traverse_file_hierarchy(
                XML_TRAVERSAL_WITH_LANGUAGES_FILE,
                False,
                self.silent_handler_function,
                f_traverse.traverse_XML_file,
                ".//treqs-element",
            )

            self.assertEqual(success, 0)

        self.assertEqual(len(captured.records), 3)
        self.assertEqual(
            captured.records[0].getMessage(), "file_traverser created"
        )
        self.assertEqual(
            captured.records[1].getMessage(),
            f"\n\nCalling XML traversal with filename {XML_TRAVERSAL_WITH_LANGUAGES_FILE}",
        )
        self.assertEqual(
            captured.records[2].getMessage(),
            f"   ### Processing elements in File {XML_TRAVERSAL_WITH_LANGUAGES_FILE}",
        )

    # <treqs-element id="189b592e-6285-4b34-88b3-2c2f81b9d37d" type="unittest">
    # File traversal gracefully logs and continues without abruption to T-Reqs
    # <treqs-link type="tests" target="4d8be51c-df13-41e9-ac02-00ffa31c3b80" />
    # </treqs-element>
    @patch("builtins.open")
    def test_XML_traversal_with_fault_tolerance(self, mock_file):
        mock_file.side_effect = [
            mock_file.return_value,  # First call that reads the treqs-ignore file should succeed
            OSError("Permission denied"),  # Second call simulates an exception
        ]
        try:
            with self.assertLogs(
                "treqs-on-git.treqs-ng", level=10
            ) as captured:
                f_traverse = file_traverser()
                f_traverse.traverse_XML_file(
                    "this_file_cannot_be_opened.md",
                    self.silent_handler_function,
                )
        except Exception:
            self.fail(
                "The expcetion should be handled gracefully in file traversal"
            )

        self.assertEqual(len(captured.records), 4)
        self.assertEqual(
            captured.records[0].getMessage(), "file_traverser created"
        )
        self.assertEqual(
            captured.records[1].getMessage(),
            "\n\nCalling XML traversal with filename this_file_cannot_be_opened.md",
        )
        self.assertEqual(
            captured.records[2].getMessage(),
            "   ### Processing elements in File this_file_cannot_be_opened.md",
        )
        self.assertEqual(
            captured.records[3].getMessage(),
            "   ### Skipping elements in File this_file_cannot_be_opened.md due to: ('Permission denied',)",
        )

    def test_robustness_on_plantuml(self):
        with self.assertLogs("treqs-on-git.treqs-ng", level=10) as captured:
            f_traverse = file_traverser()
            success = f_traverse.traverse_file_hierarchy(
                REALISTIC_PLANTUML_EXAMPLE,
                True,
                self.print_handler_function,
                f_traverse.traverse_XML_file,
                ".//treqs-element",
            )

            self.assertEqual(success, 0)

        self.assertEqual(len(captured.records), 3)
        self.assertEqual(
            captured.records[0].getMessage(), "file_traverser created"
        )
        self.assertEqual(
            captured.records[1].getMessage(),
            f"\n\nCalling XML traversal with filename {REALISTIC_PLANTUML_EXAMPLE}",
        )
        self.assertEqual(
            captured.records[2].getMessage(),
            f"   ### Processing elements in File {REALISTIC_PLANTUML_EXAMPLE}",
        )


if __name__ == "__main__":
    unittest.main()

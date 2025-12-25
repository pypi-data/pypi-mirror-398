import unittest
from pathlib import Path

from click.testing import CliRunner

from treqs.list_elements import list_elements, list_elements_plantuml_strat
from treqs.main import treqs

# Constants
LIST_ELEMENTS_FILE = str(Path("tests/test_data/2-test-list-treq-elements.md"))
LIST_ELEMENTS_OF_TYPE = str(
    Path("tests/test_data/2-test-list-treq-elements.md")
)
ELEMENTS_WITH_NONEXISTING_UID = str(
    Path("tests/test_data/2-test-list-treq-elements.md")
)
ATTRIBUTE_TEST_FILE = str(Path("tests/test_data/2-test-list-treq-elements.md"))

ELEMENTS_WITH_ID = str(Path("tests/test_data/2-test-list-treq-elements.md"))
ELEMENTS_WITH_OUTGOING_LINKS = str(
    Path("tests/test_data/2-test-list-treq-elements.md")
)
LIST_ELEMENTS_WITH_INCOMING_LINKS_FILE = str(
    Path("tests/test_data/2-test-list-treq-elements.md")
)
TREQS_ELEMENT_WITH_SAME_PREFIX = str(
    Path(
        "tests/test_data/8-test-list-inlinks-of-treqs-element-with-same-prefix.md"
    )
)
ELEMENTS_IN_NON_XML_FILE = str(
    Path("tests/test_data/6-test-traverse-treqs.md")
)

LIST_FILE_PATTERN_MD_FILE = str(
    Path("./tests/test_data/6-test-traverse-treqs.md")
)
LIST_FILE_PATTERN_PY_FILE = str(
    Path("./tests/test_data/6-test-traverse-treqs.py")
)
FILE_PATTERN_BASE_DIR = Path("./tests/test_data/test-recursive-traverser")
LIST_FILE_PATTERN_RECURSIVE_DIR = str(FILE_PATTERN_BASE_DIR)
RECURSIVE_TRAVERSER_MD_2 = str(FILE_PATTERN_BASE_DIR / "test-treq-file-2.md")
RECURSIVE_TRAVERSER_MD_1 = str(FILE_PATTERN_BASE_DIR / "test-treq-file-1.md")
RECURSIVE_TRAVERSER_PY_3 = str(FILE_PATTERN_BASE_DIR / "test-treq-file-3.py")

FILES_CONTAINING_XML_OPENING_TAGS = str(
    Path("tests/test_data/real-world-samples/java_with_generic_code.java")
)
CORRECT_LINE_NUMBER_WITH_PLANTUML = str(
    Path("tests/test_data/multiple-targets.md")
)
ELEMENTS_INLINKS_CHILD_FILE = str(
    Path("tests/test_data/follow-links/child.md")
)
ELEMENTS_INLINKS_PARENT_FILE = str(
    Path("tests/test_data/follow-links/parent.md")
)
ELEMENTS_EMPTY_LIST_FILE = str(
    Path("tests/test_data/2-test-list-treq-elements.md")
)
ELEMENTS_AND_FOLLOW_LINKS_FILE = str(
    Path("tests/test_data/2-test-list-treq-elements.md")
)
LIST_ELEMENTS_FILE_PLANT_UML = "tests/test_data/2-test-list-treq-elements.md"


class TestListElements(unittest.TestCase):
    # <treqs-element id="38e94278a22f11eba9dca7925d1c5fe9" type="unittest">
    # Basic listing.
    # <treqs-link type="tests" target="e21d72f0509411edbe22c9328ceec9a7" />
    # <treqs-link type="tests" target="001bb234509611edbe22c9328ceec9a7" />
    # <treqs-link type="tests" target="35590bca-960f-11ea-bb37-0242ac130002" />
    # <treqs-link type="tests" target="a0820e06-9614-11ea-bb37-0242ac130002" />
    # <treqs-link type="tests" target="63ef8bfa76ae11ebb811cf2f044815f7" />
    # <treqs-link type="tests" target="bc89e02a76c811ebb811cf2f044815f7" />
    # </treqs-element>
    def test_list_elements(self):
        with self.assertLogs("treqs-on-git.treqs-ng", level=10) as captured:
            # with self.assertRaises(SystemExit) as cm:
            le = list_elements()
            returnCode = le.list_elements(
                LIST_ELEMENTS_FILE, None, "false", None, False, False, None
            )
        self.assertEqual(returnCode, 0)
        self.assertEqual(1, le.traverser.filecount)
        self.assertEqual(len(captured.records), 19)
        self.assertEqual(
            captured.records[0].getMessage(), "file_traverser created"
        )
        self.assertEqual(
            captured.records[1].getMessage(), "treqs_element_factory created"
        )
        self.assertEqual(
            captured.records[2].getMessage(), "list_elements created"
        )
        self.assertEqual(
            captured.records[3].getMessage(),
            f"\n\nCalling XML traversal with filename {LIST_ELEMENTS_FILE}",
        )
        self.assertEqual(
            captured.records[4].getMessage(),
            f"   ### Processing elements in File {LIST_ELEMENTS_FILE}",
        )
        self.assertEqual(
            captured.records[5].getMessage(),
            "| UID | Type | Label | File:Line |",
        )
        self.assertEqual(
            captured.records[6].getMessage(), "| :--- | :--- | :--- | :--- |"
        )
        self.assertEqual(
            captured.records[7].getMessage(),
            f"| a0820e06-9614-11ea-bb37-0242ac130002 | requirement | ### 2.0 Parameters and default output of treqs list | {LIST_ELEMENTS_FILE}:2 |",
        )
        self.assertEqual(
            captured.records[8].getMessage(),
            f"| 63ef8bfa76ae11ebb811cf2f044815f7 | requirement | ### 2.1 Information listed by treqs list | {LIST_ELEMENTS_FILE}:11 |",
        )
        self.assertEqual(
            captured.records[9].getMessage(),
            f"| 437f09c6-9613-11ea-bb37-0242ac130002 | requirement | ### 2.2 Filter by type  | {LIST_ELEMENTS_FILE}:22 |",
        )
        self.assertEqual(
            captured.records[10].getMessage(),
            f"| abc40962a23511eba9dca7925d1c5fe9 | information | Note that the type should usually be defined in the TIM. treqs list does however not check for this to be the case. Use treqs check instead to make sure that all types are consistent with the TIM. treqs list allows to search for invalid types. | {LIST_ELEMENTS_FILE}:32 |",
        )
        self.assertEqual(
            captured.records[11].getMessage(),
            f"| ab6d69cffe6911efa7bfc85ea942d8ac | requirement | ### Req-2.3 Filter by attribute | {LIST_ELEMENTS_FILE}:38 |",
        )
        self.assertEqual(
            captured.records[12].getMessage(),
            f"| f62291a3fe7b11ef9bfec85ea942d8ac | requirement | This is a requirement with attributes ASIL=1, sample = smaple, and categroy = safety. | {LIST_ELEMENTS_FILE}:53 |",
        )
        self.assertEqual(
            captured.records[13].getMessage(),
            f"| a0820b4a-9614-11ea-bb37-0242ac130002 | requirement | ### 2.4 Filter by ID | {LIST_ELEMENTS_FILE}:57 |",
        )
        self.assertEqual(
            captured.records[14].getMessage(),
            f"| bc89e02a76c811ebb811cf2f044815f7 | requirement | ### 2.5 List all elements in a file | {LIST_ELEMENTS_FILE}:68 |",
        )
        self.assertEqual(
            captured.records[15].getMessage(),
            f"| 638fa22e76c911ebb811cf2f044815f7 | requirement | ### 2.6 List treqs elements in a directory | {LIST_ELEMENTS_FILE}:78 |",
        )
        self.assertEqual(
            captured.records[16].getMessage(),
            f"| 1595ed20a27111eb8d3991dd3edc620a | requirement | ### 2.7 List outgoing tracelinks | {LIST_ELEMENTS_FILE}:90 |",
        )
        self.assertEqual(
            captured.records[17].getMessage(),
            f"| d9e68f9aa27b11eb8d3991dd3edc620a | requirement | ### 2.8 List incoming tracelinks | {LIST_ELEMENTS_FILE}:104 |",
        )

    # <treqs-element id="3448f8f8a23411eba9dca7925d1c5fe9" type="unittest">
    # Tests basic listing functionality when a specific type is provided.
    # <treqs-link type="tests" target="437f09c6-9613-11ea-bb37-0242ac130002" />
    # </treqs-element>
    def test_list_elements_of_type(self):
        with self.assertLogs("treqs-on-git.treqs-ng", level=10) as captured:
            # with self.assertRaises(SystemExit) as cm:
            le = list_elements()
            returnCode = le.list_elements(
                LIST_ELEMENTS_OF_TYPE,
                "information",
                "false",
                None,
                False,
                False,
                None,
            )

        self.assertEqual(returnCode, 0)
        self.assertEqual(1, le.traverser.filecount)
        self.assertEqual(len(captured.records), 9)
        self.assertEqual(
            captured.records[0].getMessage(), "file_traverser created"
        )
        self.assertEqual(
            captured.records[1].getMessage(), "treqs_element_factory created"
        )
        self.assertEqual(
            captured.records[2].getMessage(), "list_elements created"
        )
        self.assertEqual(
            captured.records[3].getMessage(),
            f"\n\nCalling XML traversal with filename {LIST_ELEMENTS_OF_TYPE}",
        )
        self.assertEqual(
            captured.records[4].getMessage(),
            f"   ### Processing elements in File {LIST_ELEMENTS_OF_TYPE}",
        )
        self.assertEqual(
            captured.records[5].getMessage(),
            "| UID | Type | Label | File:Line |",
        )
        self.assertEqual(
            captured.records[6].getMessage(), "| :--- | :--- | :--- | :--- |"
        )
        self.assertEqual(
            captured.records[7].getMessage(),
            f"| abc40962a23511eba9dca7925d1c5fe9 | information | Note that the type should usually be defined in the TIM. treqs list does however not check for this to be the case. Use treqs check instead to make sure that all types are consistent with the TIM. treqs list allows to search for invalid types. | {LIST_ELEMENTS_OF_TYPE}:32 |",
        )

    def test_list_elements_with_nonexisting_UID(self):
        with self.assertLogs("treqs-on-git.treqs-ng", level=10) as captured:
            # with self.assertRaises(SystemExit) as cm:
            le = list_elements()
            returnCode = le.list_elements(
                ELEMENTS_WITH_NONEXISTING_UID,
                treqs_type="information",
                recursive="false",
                uid="an ID that does not exist",
                outlinks=False,
                inlinks=False,
            )

        self.assertEqual(returnCode, 0)
        self.assertEqual(1, le.traverser.filecount)
        self.assertEqual(len(captured.records), 7)
        self.assertEqual(
            captured.records[0].getMessage(), "file_traverser created"
        )
        self.assertEqual(
            captured.records[1].getMessage(), "treqs_element_factory created"
        )
        self.assertEqual(
            captured.records[2].getMessage(), "list_elements created"
        )
        self.assertEqual(
            captured.records[3].getMessage(),
            f"\n\nCalling XML traversal with filename {ELEMENTS_WITH_NONEXISTING_UID}",
        )
        self.assertEqual(
            captured.records[4].getMessage(),
            f"   ### Processing elements in File {ELEMENTS_WITH_NONEXISTING_UID}",
        )
        self.assertEqual(
            captured.records[5].getMessage(),
            "treqs list did not find relevant elements.",
        )
        self.assertRegex(
            captured.records[6].getMessage(),
            r"treqs list: read 1 files \(0 files ignored, 0 files unreadable, 0 files corrupt\) in ....s. Found 0 elements.",
        )

    # <treqs-element id="93992928fe7c11ef9967c85ea942d8ac" type="unittest">
    # Tests basic listing functionality when a specific attribute is provided.
    # <treqs-link type="tests" target="ab6d69cffe6911efa7bfc85ea942d8ac" />
    # </treqs-element>
    def test_list_elements_of_attribute(self):
        with self.assertLogs("treqs-on-git.treqs-ng", level=10) as captured:
            # with self.assertRaises(SystemExit) as cm:
            le = list_elements()
            returnCode = le.list_elements(
                ATTRIBUTE_TEST_FILE,
                treqs_type=None,
                recursive="false",
                uid=None,
                inlinks=False,
                outlinks=False,
                attributes={
                    "asil": "1",
                    "sample": "sample",
                    "category": "safety",
                },
            )

        self.assertEqual(returnCode, 0)
        self.assertEqual(1, le.traverser.filecount)
        self.assertEqual(len(captured.records), 9)
        self.assertEqual(
            captured.records[0].getMessage(), "file_traverser created"
        )
        self.assertEqual(
            captured.records[1].getMessage(), "treqs_element_factory created"
        )
        self.assertEqual(
            captured.records[2].getMessage(), "list_elements created"
        )
        self.assertEqual(
            captured.records[3].getMessage(),
            f"\n\nCalling XML traversal with filename {ATTRIBUTE_TEST_FILE}",
        )
        self.assertEqual(
            captured.records[4].getMessage(),
            f"   ### Processing elements in File {ATTRIBUTE_TEST_FILE}",
        )
        self.assertEqual(
            captured.records[5].getMessage(),
            "| UID | Type | Label | File:Line |",
        )
        self.assertEqual(
            captured.records[6].getMessage(), "| :--- | :--- | :--- | :--- |"
        )
        self.assertEqual(
            captured.records[7].getMessage(),
            f"| f62291a3fe7b11ef9bfec85ea942d8ac | requirement | This is a requirement with attributes ASIL=1, sample = smaple, and categroy = safety. | {ATTRIBUTE_TEST_FILE}:53 |",
        )

    def test_list_elements_of_invalid_attribute_format(self):
        runner = CliRunner()
        result = runner.invoke(
            treqs,
            [
                "list",
                "--attribute",
                "asil=1",
                "--attribute",
                "--attribute",
                "category=safety",
            ],
        )

        assert result.exit_code != 0
        assert (
            "Invalid attribute format: '--attribute'. Must be in 'key=value' format."
            in result.output
        )
        assert "Usage: treqs list" in result.output

    # <treqs-element id="8655cb6a0bfe11ec8f66f018989356c1" type="unittest">
    # Tests basic listing functionality when a specific id is provided.
    # <treqs-link type="tests" target="a0820b4a-9614-11ea-bb37-0242ac130002" />
    # </treqs-element>
    def test_list_elements_with_id(self):
        with self.assertLogs("treqs-on-git.treqs-ng", level=10) as captured:
            # with self.assertRaises(SystemExit) as cm:
            le = list_elements()
            returnCode = le.list_elements(
                ELEMENTS_WITH_ID,
                None,
                "false",
                "a0820b4a-9614-11ea-bb37-0242ac130002",
                False,
                False,
                None,
            )

        self.assertEqual(returnCode, 0)
        self.assertEqual(1, le.traverser.filecount)
        self.assertEqual(len(captured.records), 9)
        self.assertEqual(
            captured.records[0].getMessage(), "file_traverser created"
        )
        self.assertEqual(
            captured.records[1].getMessage(), "treqs_element_factory created"
        )
        self.assertEqual(
            captured.records[2].getMessage(), "list_elements created"
        )
        self.assertEqual(
            captured.records[3].getMessage(),
            f"\n\nCalling XML traversal with filename {ELEMENTS_WITH_ID}",
        )
        self.assertEqual(
            captured.records[4].getMessage(),
            f"   ### Processing elements in File {ELEMENTS_WITH_ID}",
        )
        self.assertEqual(
            captured.records[5].getMessage(),
            "| UID | Type | Label | File:Line |",
        )
        self.assertEqual(
            captured.records[6].getMessage(), "| :--- | :--- | :--- | :--- |"
        )
        self.assertEqual(
            captured.records[7].getMessage(),
            f"| a0820b4a-9614-11ea-bb37-0242ac130002 | requirement | ### 2.4 Filter by ID | {ELEMENTS_WITH_ID}:57 |",
        )

    # <treqs-element id="62a684fc0bfe11ec9984f018989356c1" type="unittest">
    # List outgoing tracelinks.
    # <treqs-link type="tests" target="1595ed20a27111eb8d3991dd3edc620a" />
    # </treqs-element>
    def test_list_elements_with_outgoing_links(self):
        with self.assertLogs("treqs-on-git.treqs-ng", level=10) as captured:
            # with self.assertRaises(SystemExit) as cm:
            le = list_elements()
            # Some caching problems for this test, I assume..
            returnCode = le.list_elements(
                ELEMENTS_WITH_OUTGOING_LINKS,
                None,
                False,
                "1595ed20a27111eb8d3991dd3edc620a",
                True,
                False,
                None,
            )

        self.assertEqual(returnCode, 0)
        self.assertEqual(1, le.traverser.filecount)
        self.assertEqual(len(captured.records), 14)
        self.assertEqual(
            captured.records[0].getMessage(), "file_traverser created"
        )
        self.assertEqual(
            captured.records[1].getMessage(), "treqs_element_factory created"
        )
        self.assertEqual(
            captured.records[2].getMessage(), "list_elements created"
        )
        self.assertEqual(
            captured.records[3].getMessage(),
            f"\n\nCalling XML traversal with filename {ELEMENTS_WITH_OUTGOING_LINKS}",
        )
        self.assertEqual(
            captured.records[4].getMessage(),
            f"   ### Processing elements in File {ELEMENTS_WITH_OUTGOING_LINKS}",
        )
        self.assertEqual(
            captured.records[5].getMessage(),
            "| UID | Type | Label | File:Line |",
        )
        self.assertEqual(
            captured.records[6].getMessage(), "| :--- | :--- | :--- | :--- |"
        )
        self.assertEqual(
            captured.records[7].getMessage(),
            f"| 1595ed20a27111eb8d3991dd3edc620a | requirement | ### 2.7 List outgoing tracelinks | {ELEMENTS_WITH_OUTGOING_LINKS}:90 |",
        )
        self.assertEqual(
            captured.records[8].getMessage(),
            "| --outlink--> (35590bca-960f-11ea-bb37-0242ac130002) | hasParent | Target: Target treqs element not found. Has the containing file been included in the scope? | -- |",
        )
        self.assertEqual(
            captured.records[9].getMessage(),
            f"| --outlink--> (63ef8bfa76ae11ebb811cf2f044815f7) | relatesTo | Target: ### 2.1 Information listed by treqs list | {ELEMENTS_WITH_OUTGOING_LINKS}:11 |",
        )
        self.assertEqual(
            captured.records[10].getMessage(),
            f"| --outlink--> (d9e68f9aa27b11eb8d3991dd3edc620a) | relatesTo | Target: ### 2.8 List incoming tracelinks | {ELEMENTS_WITH_OUTGOING_LINKS}:104 |",
        )
        self.assertEqual(
            captured.records[11].getMessage(),
            "| --outlink--> (1e9885f69d3311eb859fc4b301c00591) | addresses | Target: Target treqs element not found. Has the containing file been included in the scope? | -- |",
        )
        self.assertEqual(
            captured.records[12].getMessage(),
            "| --outlink--> (54a4e59a9d3311ebb4d2c4b301c00591) | addresses | Target: Target treqs element not found. Has the containing file been included in the scope? | -- |",
        )

    # <treqs-element id="5f38eea40bfe11ecbc65f018989356c1" type="unittest">
    # Test listing incoming tracelinks.
    # <treqs-link type="tests" target="d9e68f9aa27b11eb8d3991dd3edc620a" />
    # </treqs-element>
    def test_list_elements_with_incoming_links(self):
        with self.assertLogs("treqs-on-git.treqs-ng", level=10) as captured:
            # with self.assertRaises(SystemExit) as cm:
            le = list_elements()
            returnCode = le.list_elements(
                LIST_ELEMENTS_WITH_INCOMING_LINKS_FILE,
                None,
                False,
                "d9e68f9aa27b11eb8d3991dd3edc620a",
                False,
                True,
                None,
            )

        self.assertEqual(returnCode, 0)
        self.assertEqual(1, le.traverser.filecount)
        self.assertEqual(len(captured.records), 10)
        self.assertEqual(
            captured.records[0].getMessage(), "file_traverser created"
        )
        self.assertEqual(
            captured.records[1].getMessage(), "treqs_element_factory created"
        )
        self.assertEqual(
            captured.records[2].getMessage(), "list_elements created"
        )
        self.assertEqual(
            captured.records[3].getMessage(),
            f"\n\nCalling XML traversal with filename {LIST_ELEMENTS_WITH_INCOMING_LINKS_FILE}",
        )
        self.assertEqual(
            captured.records[4].getMessage(),
            f"   ### Processing elements in File {LIST_ELEMENTS_WITH_INCOMING_LINKS_FILE}",
        )
        self.assertEqual(
            captured.records[5].getMessage(),
            "| UID | Type | Label | File:Line |",
        )
        self.assertEqual(
            captured.records[6].getMessage(), "| :--- | :--- | :--- | :--- |"
        )
        self.assertEqual(
            captured.records[7].getMessage(),
            f"| d9e68f9aa27b11eb8d3991dd3edc620a | requirement | ### 2.8 List incoming tracelinks | {LIST_ELEMENTS_WITH_INCOMING_LINKS_FILE}:104 |",
        )
        self.assertEqual(
            captured.records[8].getMessage(),
            f"| --inlink--> (1595ed20a27111eb8d3991dd3edc620a) | relatesTo | Source: ### 2.7 List outgoing tracelinks | {LIST_ELEMENTS_WITH_INCOMING_LINKS_FILE}:90 |",
        )

    # Tests that inlinks are listed correctly for elements that start with the same prefix
    def test_list_inlinks_of_treqs_element_with_same_prefix(self):
        with self.assertLogs("treqs-on-git.treqs-ng", level=10) as captured:
            # with self.assertRaises(SystemExit) as cm:
            le = list_elements()
            returnCode = le.list_elements(
                TREQS_ELEMENT_WITH_SAME_PREFIX,
                None,
                False,
                "need",
                False,
                True,
                None,
            )

        self.assertEqual(returnCode, 0)
        self.assertEqual(1, le.traverser.filecount)
        self.assertEqual(len(captured.records), 10)
        self.assertEqual(
            captured.records[0].getMessage(), "file_traverser created"
        )
        self.assertEqual(
            captured.records[1].getMessage(), "treqs_element_factory created"
        )
        self.assertEqual(
            captured.records[2].getMessage(), "list_elements created"
        )
        self.assertEqual(
            captured.records[3].getMessage(),
            f"\n\nCalling XML traversal with filename {TREQS_ELEMENT_WITH_SAME_PREFIX}",
        )
        self.assertEqual(
            captured.records[4].getMessage(),
            f"   ### Processing elements in File {TREQS_ELEMENT_WITH_SAME_PREFIX}",
        )
        self.assertEqual(
            captured.records[5].getMessage(),
            "| UID | Type | Label | File:Line |",
        )
        self.assertEqual(
            captured.records[6].getMessage(), "| :--- | :--- | :--- | :--- |"
        )
        self.assertEqual(
            captured.records[7].getMessage(),
            f"| need | stakeholder-need | A Generic Need | {TREQS_ELEMENT_WITH_SAME_PREFIX}:15 |",
        )
        self.assertEqual(
            captured.records[8].getMessage(),
            f"| --inlink--> (my-stakeholder-requirement) | addresses | Source: A simple stakeholder requirement | {TREQS_ELEMENT_WITH_SAME_PREFIX}:1 |",
        )

    # Tests that treqs-elements in non-XML files are found and listed.
    def test_list_elements_in_non_xml(self):
        with self.assertLogs("treqs-on-git.treqs-ng", level=10) as captured:
            # with self.assertRaises(SystemExit) as cm:
            le = list_elements()
            returnCode = le.list_elements(
                ELEMENTS_IN_NON_XML_FILE,
                None,
                "false",
                None,
                False,
                False,
                None,
            )

        self.assertEqual(returnCode, 0)
        self.assertEqual(1, le.traverser.filecount)

        self.assertEqual(len(captured.records), 11)
        self.assertEqual(
            captured.records[0].getMessage(), "file_traverser created"
        )
        self.assertEqual(
            captured.records[1].getMessage(), "treqs_element_factory created"
        )
        self.assertEqual(
            captured.records[2].getMessage(), "list_elements created"
        )
        self.assertEqual(
            captured.records[3].getMessage(),
            f"\n\nCalling XML traversal with filename {ELEMENTS_IN_NON_XML_FILE}",
        )
        self.assertEqual(
            captured.records[4].getMessage(),
            f"   ### Processing elements in File {ELEMENTS_IN_NON_XML_FILE}",
        )
        self.assertEqual(
            captured.records[5].getMessage(),
            "| UID | Type | Label | File:Line |",
        )
        self.assertEqual(
            captured.records[6].getMessage(), "| :--- | :--- | :--- | :--- |"
        )
        self.assertEqual(
            captured.records[7].getMessage(),
            f"| 0276e84ac79011ebb719f018989356c1 | requirement | ### 6-test-1 TReqs file traverser shall be able to handle documents without root tag. | {ELEMENTS_IN_NON_XML_FILE}:1 |",
        )
        self.assertEqual(
            captured.records[8].getMessage(),
            f"| ff403b04c78f11ebbdc9f018989356c1 | requirement | ### 6-test-2 TReqs file traverser shall be able to handle treqs-elements that are not under the root. | {ELEMENTS_IN_NON_XML_FILE}:9 |",
        )
        self.assertEqual(
            captured.records[9].getMessage(),
            f"| c5ae0c10c79211eb9631f018989356c1 | requirement | ### 6-test-3 TReqs file traverser shall be able to handle treqs-elements in non-md files. | {ELEMENTS_IN_NON_XML_FILE}:17 |",
        )

    def test_list_file_pattern(self):
        with self.assertLogs("treqs-on-git.treqs-ng", level=10) as captured:
            # with self.assertRaises(SystemExit) as cm:
            le = list_elements()
            returnCode = le.list_elements(
                (
                    LIST_FILE_PATTERN_MD_FILE,
                    LIST_FILE_PATTERN_PY_FILE,
                    LIST_FILE_PATTERN_RECURSIVE_DIR,
                ),
                None,
                "True",
                None,
                False,
                False,
                None,
            )
        self.assertEqual(returnCode, 0)
        self.assertEqual(2, le.traverser.filecount)
        self.assertEqual(len(captured.records), 17)
        self.assertEqual(
            captured.records[0].getMessage(), "file_traverser created"
        )
        self.assertEqual(
            captured.records[1].getMessage(), "treqs_element_factory created"
        )
        self.assertEqual(
            captured.records[2].getMessage(), "list_elements created"
        )

        records = [r.getMessage() for r in captured.records[3:10]]
        self.assertIn(
            f"\n\nCalling XML traversal with filename {LIST_FILE_PATTERN_MD_FILE}",
            records,
        )
        self.assertIn(
            f"   ### Processing elements in File {LIST_FILE_PATTERN_MD_FILE}",
            records,
        )
        self.assertIn(
            f"\n\nCalling XML traversal with filename {LIST_FILE_PATTERN_PY_FILE}",
            records,
        )
        self.assertIn(
            f"   ### Processing elements in File {LIST_FILE_PATTERN_PY_FILE}",
            records,
        )
        self.assertIn(
            f"   ### Ignoring file {RECURSIVE_TRAVERSER_MD_2} (.treqs-ignore)",
            records,
        )
        self.assertIn(
            f"   ### Ignoring file {RECURSIVE_TRAVERSER_MD_1} (.treqs-ignore)",
            records,
        )
        self.assertIn(
            f"   ### Ignoring file {RECURSIVE_TRAVERSER_PY_3} (.treqs-ignore)",
            records,
        )

        self.assertEqual(
            captured.records[10].getMessage(),
            "| UID | Type | Label | File:Line |",
        )
        self.assertEqual(
            captured.records[11].getMessage(), "| :--- | :--- | :--- | :--- |"
        )
        self.assertEqual(
            captured.records[12].getMessage(),
            f"| 0276e84ac79011ebb719f018989356c1 | requirement | ### 6-test-1 TReqs file traverser shall be able to handle documents without root tag. | {LIST_FILE_PATTERN_MD_FILE}:1 |",
        )
        self.assertEqual(
            captured.records[13].getMessage(),
            f"| ff403b04c78f11ebbdc9f018989356c1 | requirement | ### 6-test-2 TReqs file traverser shall be able to handle treqs-elements that are not under the root. | {LIST_FILE_PATTERN_MD_FILE}:9 |",
        )
        self.assertEqual(
            captured.records[14].getMessage(),
            f"| c5ae0c10c79211eb9631f018989356c1 | requirement | ### 6-test-3 TReqs file traverser shall be able to handle treqs-elements in non-md files. | {LIST_FILE_PATTERN_MD_FILE}:17 |",
        )
        self.assertEqual(
            captured.records[15].getMessage(),
            f"| 9c0adc12c79211ebb9cbf018989356c1 | unittest |     # Does nothing - test data. | {LIST_FILE_PATTERN_PY_FILE}:4 |",
        )

    # <treqs-element id="f20540f9a71511ef9431d89ef374263e" type="unittest">
    # Test listing elements in files containing XML opening and closing tags, i.e. the elements are extracted and the file is not ignored due to XML parsing errors, as it was previously.
    # <treqs-link type="tests" target="ab59f9c4a71111efaf2ed89ef374263e" />
    # </treqs-element>
    def test_list_elements_in_files_containing_xml_opening_tags(self):
        with self.assertLogs("treqs-on-git.treqs-ng", level=10) as captured:
            # with self.assertRaises(SystemExit) as cm:
            le = list_elements()
            returnCode = le.list_elements(
                FILES_CONTAINING_XML_OPENING_TAGS,
                None,
                "false",
                None,
                False,
                False,
                None,
            )

        self.assertEqual(returnCode, 0)
        self.assertEqual(1, le.traverser.filecount)

        self.assertEqual(len(captured.records), 9)
        self.assertEqual(
            captured.records[0].getMessage(), "file_traverser created"
        )
        self.assertEqual(
            captured.records[1].getMessage(), "treqs_element_factory created"
        )
        self.assertEqual(
            captured.records[2].getMessage(), "list_elements created"
        )
        self.assertEqual(
            captured.records[3].getMessage(),
            f"\n\nCalling XML traversal with filename {FILES_CONTAINING_XML_OPENING_TAGS}",
        )
        self.assertEqual(
            captured.records[4].getMessage(),
            f"   ### Processing elements in File {FILES_CONTAINING_XML_OPENING_TAGS}",
        )
        self.assertEqual(
            captured.records[5].getMessage(),
            "| UID | Type | Label | File:Line |",
        )
        self.assertEqual(
            captured.records[6].getMessage(), "| :--- | :--- | :--- | :--- |"
        )
        self.assertEqual(
            captured.records[7].getMessage(),
            f"| sample-id | unittest | // My Contract Validator | {FILES_CONTAINING_XML_OPENING_TAGS}:3 |",
        )

    # <treqs-element id="aedbdbb7a71611efa544d89ef374263e" type="unittest">
    # Test listing correct line number for elements in files with PlantUML: The elements extracted from the file that has PlantUML get the right line number associated to them.
    # <treqs-link type="tests" target="ab59f9c4a71111efaf2ed89ef374263e" />
    # </treqs-element>
    def test_list_correct_line_number_for_elements_in_file_with_plantuml(self):
        with self.assertLogs("treqs-on-git.treqs-ng", level=10) as captured:
            # with self.assertRaises(SystemExit) as cm:
            le = list_elements()
            returnCode = le.list_elements(
                CORRECT_LINE_NUMBER_WITH_PLANTUML,
                None,
                "false",
                None,
                False,
                False,
                None,
            )

        self.assertEqual(returnCode, 0)
        self.assertEqual(1, le.traverser.filecount)

        self.assertEqual(len(captured.records), 11)
        self.assertEqual(
            captured.records[0].getMessage(), "file_traverser created"
        )
        self.assertEqual(
            captured.records[1].getMessage(), "treqs_element_factory created"
        )
        self.assertEqual(
            captured.records[2].getMessage(), "list_elements created"
        )
        self.assertEqual(
            captured.records[3].getMessage(),
            f"\n\nCalling XML traversal with filename {CORRECT_LINE_NUMBER_WITH_PLANTUML}",
        )
        self.assertEqual(
            captured.records[4].getMessage(),
            f"   ### Processing elements in File {CORRECT_LINE_NUMBER_WITH_PLANTUML}",
        )
        self.assertEqual(
            captured.records[5].getMessage(),
            "| UID | Type | Label | File:Line |",
        )
        self.assertEqual(
            captured.records[6].getMessage(), "| :--- | :--- | :--- | :--- |"
        )
        self.assertEqual(
            captured.records[7].getMessage(),
            f"| a | A | @startuml | {CORRECT_LINE_NUMBER_WITH_PLANTUML}:1 |",
        )
        self.assertEqual(
            captured.records[8].getMessage(),
            f"| b | B | None | {CORRECT_LINE_NUMBER_WITH_PLANTUML}:18 |",
        )
        self.assertEqual(
            captured.records[9].getMessage(),
            f"| c | C | None | {CORRECT_LINE_NUMBER_WITH_PLANTUML}:22 |",
        )


class TestTestListElementsPlantUML(unittest.TestCase):
    # <treqs-element id="1dc5e4d6d23011eeadb88de628732e03" type="unittest">
    # Test generating PlantUML from treqs list command
    # <treqs-link type="tests" target="6473290ed22e11eeadb88de628732e03" />
    # </treqs-element>
    def test_list_elements(self):
        lestrat = list_elements_plantuml_strat()
        with self.assertLogs("treqs-on-git.treqs-ng", level=10) as captured:
            # with self.assertRaises(SystemExit) as cm:
            le = list_elements(lestrat)
            returnCode = le.list_elements(
                LIST_ELEMENTS_FILE_PLANT_UML,
                treqs_type=None,
                outlinks=True,
                inlinks=None,
            )
        self.assertEqual(returnCode, 0)
        self.assertEqual(len(captured.records), 96)
        self.assertEqual(
            captured.records[0].getMessage(), "file_traverser created"
        )
        self.assertEqual(
            captured.records[1].getMessage(), "treqs_element_factory created"
        )
        self.assertEqual(
            captured.records[2].getMessage(), "list_elements created"
        )
        self.assertEqual(
            captured.records[3].getMessage(),
            f"\n\nCalling XML traversal with filename {LIST_ELEMENTS_FILE_PLANT_UML}",
        )
        self.assertEqual(
            captured.records[4].getMessage(),
            f"   ### Processing elements in File {LIST_ELEMENTS_FILE_PLANT_UML}",
        )
        records = [r.getMessage() for r in captured.records[5:100]]
        self.assertIn("@startuml", records)
        self.assertIn(
            'map "**### 2.0 Parameters and default output of treqs list**" as a0820e06_9614_11ea_bb37_0242ac130002 {',
            records,
        )
        self.assertIn(
            'uid => ""a0820e06-9614-11ea-bb37-0242ac130002""', records
        )
        self.assertIn("type => //requirement//", records)
        self.assertIn(
            "location => tests/\\ntest_data/\\n2-test-list-treq-elements.md:2",
            records,
        )
        self.assertIn("}", records)
        self.assertIn(
            'map "**### 2.1 Information listed by treqs list**" as 63ef8bfa76ae11ebb811cf2f044815f7 {',
            records,
        )
        self.assertIn('uid => ""63ef8bfa76ae11ebb811cf2f044815f7""', records)
        self.assertIn("type => //requirement//", records)
        self.assertIn(
            "location => tests/\\ntest_data/\\n2-test-list-treq-elements.md:11",
            records,
        )
        self.assertIn("}", records)
        self.assertIn(
            'map "**### 2.2 Filter by type **" as 437f09c6_9613_11ea_bb37_0242ac130002 {',
            records,
        )
        self.assertIn(
            'uid => ""437f09c6-9613-11ea-bb37-0242ac130002""', records
        )
        self.assertIn("type => //requirement//", records)
        self.assertIn(
            "location => tests/\\ntest_data/\\n2-test-list-treq-elements.md:22",
            records,
        )
        self.assertIn("}", records)
        self.assertIn(
            'map "**Note that the type should usually be defined in the TIM. treqs list does however not check for this to be the case. Use treqs check instead to make sure that all types are consistent with the TIM. treqs list allows to search for invalid types.**" as abc40962a23511eba9dca7925d1c5fe9 {',
            records,
        )
        self.assertIn('uid => ""abc40962a23511eba9dca7925d1c5fe9""', records)
        self.assertIn("type => //information//", records)
        self.assertIn(
            "location => tests/\\ntest_data/\\n2-test-list-treq-elements.md:32",
            records,
        )
        self.assertIn("}", records)
        self.assertIn(
            'map "**### Req-2.3 Filter by attribute**" as ab6d69cffe6911efa7bfc85ea942d8ac {',
            records,
        )
        self.assertIn('uid => ""ab6d69cffe6911efa7bfc85ea942d8ac""', records)
        self.assertIn("type => //requirement//", records)
        self.assertIn(
            "location => tests/\\ntest_data/\\n2-test-list-treq-elements.md:38",
            records,
        )
        self.assertIn("}", records)
        self.assertIn(
            'map "**This is a requirement with attributes ASIL=1, sample = smaple, and categroy = safety.**" as f62291a3fe7b11ef9bfec85ea942d8ac {',
            records,
        )
        self.assertIn('uid => ""f62291a3fe7b11ef9bfec85ea942d8ac""', records)
        self.assertIn("type => //requirement//", records)
        self.assertIn(
            "location => tests/\\ntest_data/\\n2-test-list-treq-elements.md:53",
            records,
        )
        self.assertIn("}", records)
        self.assertIn(
            'map "**### 2.4 Filter by ID**" as a0820b4a_9614_11ea_bb37_0242ac130002 {',
            records,
        )
        self.assertIn(
            'uid => ""a0820b4a-9614-11ea-bb37-0242ac130002""', records
        )
        self.assertIn("type => //requirement//", records)
        self.assertIn(
            "location => tests/\\ntest_data/\\n2-test-list-treq-elements.md:57",
            records,
        )
        self.assertIn("}", records)
        self.assertIn(
            'map "**### 2.5 List all elements in a file**" as bc89e02a76c811ebb811cf2f044815f7 {',
            records,
        )
        self.assertIn('uid => ""bc89e02a76c811ebb811cf2f044815f7""', records)
        self.assertIn("type => //requirement//", records)
        self.assertIn(
            "location => tests/\\ntest_data/\\n2-test-list-treq-elements.md:68",
            records,
        )
        self.assertIn("}", records)
        self.assertIn(
            'map "**### 2.6 List treqs elements in a directory**" as 638fa22e76c911ebb811cf2f044815f7 {',
            records,
        )
        self.assertIn('uid => ""638fa22e76c911ebb811cf2f044815f7""', records)
        self.assertIn("type => //requirement//", records)
        self.assertIn(
            "location => tests/\\ntest_data/\\n2-test-list-treq-elements.md:78",
            records,
        )
        self.assertIn("}", records)
        self.assertIn(
            'map "**### 2.7 List outgoing tracelinks**" as 1595ed20a27111eb8d3991dd3edc620a {',
            records,
        )
        self.assertIn('uid => ""1595ed20a27111eb8d3991dd3edc620a""', records)
        self.assertIn("type => //requirement//", records)
        self.assertIn(
            "location => tests/\\ntest_data/\\n2-test-list-treq-elements.md:90",
            records,
        )
        self.assertIn("}", records)
        self.assertIn(
            'map "**### 2.8 List incoming tracelinks**" as d9e68f9aa27b11eb8d3991dd3edc620a {',
            records,
        )
        self.assertIn('uid => ""d9e68f9aa27b11eb8d3991dd3edc620a""', records)
        self.assertIn("type => //requirement//", records)
        self.assertIn(
            "location => tests/\\ntest_data/\\n2-test-list-treq-elements.md:104",
            records,
        )
        self.assertIn("}", records)
        self.assertIn(
            "bc89e02a76c811ebb811cf2f044815f7 --> a0820e06_9614_11ea_bb37_0242ac130002 : relatesTo",
            records,
        )
        self.assertIn(
            "1595ed20a27111eb8d3991dd3edc620a --> 63ef8bfa76ae11ebb811cf2f044815f7 : relatesTo",
            records,
        )
        self.assertIn(
            "d9e68f9aa27b11eb8d3991dd3edc620a --> 63ef8bfa76ae11ebb811cf2f044815f7 : relatesTo",
            records,
        )
        self.assertIn(
            "638fa22e76c911ebb811cf2f044815f7 --> bc89e02a76c811ebb811cf2f044815f7 : relatesTo",
            records,
        )
        self.assertIn(
            "1595ed20a27111eb8d3991dd3edc620a --> d9e68f9aa27b11eb8d3991dd3edc620a : relatesTo",
            records,
        )
        self.assertIn(
            'map "**OUT OF SCOPE ELEMENT**" as 35590bca_960f_11ea_bb37_0242ac130002 {',
            records,
        )
        self.assertIn(
            'uid => ""35590bca-960f-11ea-bb37-0242ac130002""', records
        )
        self.assertIn("}", records)
        self.assertIn(
            "a0820e06_9614_11ea_bb37_0242ac130002 --> 35590bca_960f_11ea_bb37_0242ac130002 : hasParent",
            records,
        )
        self.assertIn(
            'map "**OUT OF SCOPE ELEMENT**" as 1e9885f69d3311eb859fc4b301c00591 {',
            records,
        )
        self.assertIn('uid => ""1e9885f69d3311eb859fc4b301c00591""', records)
        self.assertIn("}", records)
        self.assertIn(
            "a0820e06_9614_11ea_bb37_0242ac130002 --> 1e9885f69d3311eb859fc4b301c00591 : addresses",
            records,
        )
        self.assertIn(
            "63ef8bfa76ae11ebb811cf2f044815f7 --> 35590bca_960f_11ea_bb37_0242ac130002 : hasParent",
            records,
        )
        self.assertIn(
            "63ef8bfa76ae11ebb811cf2f044815f7 --> 1e9885f69d3311eb859fc4b301c00591 : addresses",
            records,
        )
        self.assertIn(
            "437f09c6_9613_11ea_bb37_0242ac130002 --> 35590bca_960f_11ea_bb37_0242ac130002 : hasParent",
            records,
        )
        self.assertIn(
            "437f09c6_9613_11ea_bb37_0242ac130002 --> 1e9885f69d3311eb859fc4b301c00591 : addresses",
            records,
        )
        self.assertIn(
            "a0820b4a_9614_11ea_bb37_0242ac130002 --> 35590bca_960f_11ea_bb37_0242ac130002 : hasParent",
            records,
        )
        self.assertIn(
            "a0820b4a_9614_11ea_bb37_0242ac130002 --> 1e9885f69d3311eb859fc4b301c00591 : addresses",
            records,
        )
        self.assertIn(
            'map "**OUT OF SCOPE ELEMENT**" as 54a4e59a9d3311ebb4d2c4b301c00591 {',
            records,
        )
        self.assertIn('uid => ""54a4e59a9d3311ebb4d2c4b301c00591""', records)
        self.assertIn("}", records)
        self.assertIn(
            "a0820b4a_9614_11ea_bb37_0242ac130002 --> 54a4e59a9d3311ebb4d2c4b301c00591 : addresses",
            records,
        )
        self.assertIn(
            "bc89e02a76c811ebb811cf2f044815f7 --> 35590bca_960f_11ea_bb37_0242ac130002 : hasParent",
            records,
        )
        self.assertIn(
            "bc89e02a76c811ebb811cf2f044815f7 --> a0820e06_9614_11ea_bb37_0242ac130002 : relatesTo",
            records,
        )
        self.assertIn(
            "638fa22e76c911ebb811cf2f044815f7 --> 35590bca_960f_11ea_bb37_0242ac130002 : hasParent",
            records,
        )
        self.assertIn(
            "638fa22e76c911ebb811cf2f044815f7 --> bc89e02a76c811ebb811cf2f044815f7 : relatesTo",
            records,
        )
        self.assertIn(
            "1595ed20a27111eb8d3991dd3edc620a --> 35590bca_960f_11ea_bb37_0242ac130002 : hasParent",
            records,
        )
        self.assertIn(
            "1595ed20a27111eb8d3991dd3edc620a --> 63ef8bfa76ae11ebb811cf2f044815f7 : relatesTo",
            records,
        )
        self.assertIn(
            "1595ed20a27111eb8d3991dd3edc620a --> d9e68f9aa27b11eb8d3991dd3edc620a : relatesTo",
            records,
        )
        self.assertIn(
            "1595ed20a27111eb8d3991dd3edc620a --> 1e9885f69d3311eb859fc4b301c00591 : addresses",
            records,
        )
        self.assertIn(
            "1595ed20a27111eb8d3991dd3edc620a --> 54a4e59a9d3311ebb4d2c4b301c00591 : addresses",
            records,
        )
        self.assertIn(
            "d9e68f9aa27b11eb8d3991dd3edc620a --> 35590bca_960f_11ea_bb37_0242ac130002 : hasParent",
            records,
        )
        self.assertIn(
            "d9e68f9aa27b11eb8d3991dd3edc620a --> 63ef8bfa76ae11ebb811cf2f044815f7 : relatesTo",
            records,
        )
        self.assertIn(
            "d9e68f9aa27b11eb8d3991dd3edc620a --> 1e9885f69d3311eb859fc4b301c00591 : addresses",
            records,
        )
        self.assertIn(
            "d9e68f9aa27b11eb8d3991dd3edc620a --> 54a4e59a9d3311ebb4d2c4b301c00591 : addresses",
            records,
        )
        self.assertIn("@enduml", records)

    def test_list_elements_inlinks(self):
        lestrat = list_elements_plantuml_strat()
        with self.assertLogs("treqs-on-git.treqs-ng", level=10) as captured:
            #    with self.assertRaises(SystemExit) as cm:
            le = list_elements(lestrat)
            returnCode = le.list_elements(
                (ELEMENTS_INLINKS_CHILD_FILE, ELEMENTS_INLINKS_PARENT_FILE),
                treqs_type=None,
                outlinks=False,
                inlinks=True,
                followlinks=True,
                uid="9a652b01023911f082ef1c697aa14cc2",
            )
            # TODO next line should do the same as the line above.
            # le.list_elements('tests/test_data/follow-links/', treqs_type=None, outlinks=False, inlinks=True, followlinks=True, uid='9a652b01023911f082ef1c697aa14cc2')

        records = [r.getMessage() for r in captured.records[5:100]]

        self.assertEqual(returnCode, 0)
        self.assertEqual(2, le.traverser.filecount)
        self.assertEqual(1, len(le.element_list))
        self.assertEqual(
            captured.records[0].getMessage(), "file_traverser created"
        )
        self.assertEqual(
            captured.records[1].getMessage(), "treqs_element_factory created"
        )
        self.assertEqual(
            captured.records[2].getMessage(), "list_elements created"
        )
        self.assertEqual(
            captured.records[3].getMessage(),
            f"\n\nCalling XML traversal with filename {ELEMENTS_INLINKS_CHILD_FILE}",
        )
        self.assertEqual(
            captured.records[4].getMessage(),
            f"   ### Processing elements in File {ELEMENTS_INLINKS_CHILD_FILE}",
        )
        self.assertIn(
            "4975e41c024c11f0a48b1c697aa14cc2 --> 9eac9eac023911f0909c1c697aa14cc2 : undefined",
            records,
        )
        self.assertIn(
            "9eac9eac023911f0909c1c697aa14cc2 --> 9a652b01023911f082ef1c697aa14cc2 : undefined",
            records,
        )

    def test_produce_safe_plantuml_ids(self):
        lestrat = list_elements_plantuml_strat()
        self.assertEqual("goodID", lestrat.safe_plantuml_uid("goodID"))
        self.assertEqual("bad_ID", lestrat.safe_plantuml_uid("bad_ID"))
        self.assertEqual("UNKNOWN_UID", lestrat.safe_plantuml_uid(None))

    def test_list_elements_empty_list(self):
        lestrat = list_elements_plantuml_strat()
        with self.assertLogs("treqs-on-git.treqs-ng", level=10) as captured:
            #   with self.assertRaises(SystemExit) as cm:
            le = list_elements(lestrat)
            returnCode = le.list_elements(
                ELEMENTS_EMPTY_LIST_FILE,
                treqs_type=None,
                outlinks=True,
                inlinks=None,
                uid="does not exist",
            )
        self.assertEqual(returnCode, 0)
        self.assertEqual(len(captured.records), 7)
        self.assertEqual(1, le.traverser.filecount)
        self.assertEqual(
            captured.records[0].getMessage(), "file_traverser created"
        )
        self.assertEqual(
            captured.records[1].getMessage(), "treqs_element_factory created"
        )
        self.assertEqual(
            captured.records[2].getMessage(), "list_elements created"
        )
        self.assertEqual(
            captured.records[3].getMessage(),
            f"\n\nCalling XML traversal with filename {ELEMENTS_EMPTY_LIST_FILE}",
        )
        self.assertEqual(
            captured.records[4].getMessage(),
            f"   ### Processing elements in File {ELEMENTS_EMPTY_LIST_FILE}",
        )
        self.assertEqual(
            captured.records[5].getMessage(),
            "treqs list did not find relevant elements.",
        )

    # <treqs-element id="beb66edfe7d411efbeec1c697aa14cc2" type="unittest">
    # Test the ability to follow links when generating PlantUML.
    # <treqs-link type="tests" target="10302d4ee7d111efb4071c697aa14cc2" />
    # </treqs-element>
    def test_list_elements_and_follow_links(self):
        lestrat = list_elements_plantuml_strat()
        # See if it makes a difference. Without follow links.
        with self.assertLogs("treqs-on-git.treqs-ng", level=10) as captured:
            # with self.assertRaises(SystemExit) as cm:
            le = list_elements(lestrat)
            returnCode = le.list_elements(
                ELEMENTS_AND_FOLLOW_LINKS_FILE,
                None,
                outlinks=True,
                inlinks=True,
                followlinks=False,
                uid="638fa22e76c911ebb811cf2f044815f7",
            )
        self.assertEqual(returnCode, 0)
        self.assertEqual(len(captured.records), 23)
        self.assertEqual(1, le.traverser.filecount)
        # Now with follow links
        with self.assertLogs("treqs-on-git.treqs-ng", level=10) as captured:
            # with self.assertRaises(SystemExit) as cm:
            le = list_elements(lestrat)
            returnCode = le.list_elements(
                ELEMENTS_AND_FOLLOW_LINKS_FILE,
                treqs_type=None,
                outlinks=True,
                inlinks=None,
                followlinks=True,
                uid="638fa22e76c911ebb811cf2f044815f7",
            )
        self.assertEqual(returnCode, 0)
        self.assertEqual(len(captured.records), 35)

        # Now check that it does not make a difference if all elements are already included.
        with self.assertLogs("treqs-on-git.treqs-ng", level=10) as captured:
            # with self.assertRaises(SystemExit) as cm:
            le = list_elements(lestrat)
            returnCode = le.list_elements(
                ELEMENTS_AND_FOLLOW_LINKS_FILE,
                treqs_type=None,
                outlinks=True,
                inlinks=False,
                followlinks=True,
            )
        self.assertEqual(returnCode, 0)
        self.assertEqual(len(captured.records), 96)

        # Now check that it does not make a difference if all elements are already included.
        with self.assertLogs("treqs-on-git.treqs-ng", level=10) as captured:
            # with self.assertRaises(SystemExit) as cm:
            le = list_elements(lestrat)
            returnCode = le.list_elements(
                ELEMENTS_AND_FOLLOW_LINKS_FILE,
                treqs_type=None,
                outlinks=True,
                inlinks=None,
                followlinks=True,
            )
        self.assertEqual(returnCode, 0)
        self.assertEqual(len(captured.records), 96)


# <treqs-element id="73a6a1eac72211f08be5a65fee9cf991" type="unittest">
# Test-6.1: Verify resolver lists external elements
# <treqs-link type="tests" target="834ef65cb75e11f099fca65fee9cf990"/>
# </treqs-element>
class TestListExternalElements(unittest.TestCase):
    """Tests for external element resolution in list_elements."""

    def test_list_elements_with_external_uid_filter(self):
        """
        Test that filtering by an external UID directly resolves
        and returns the external element.
        """
        from unittest.mock import patch

        from treqs.extension_loader import load_resolver_callback

        mock_issue_data = {
            "iid": 42,
            "title": "External Issue #42",
            "description": "External issue description",
            "state": "closed",
            "author": {"username": "testuser"},
            "web_url": "https://gitlab.com/my-project/-/issues/42",
        }

        with patch(
            "treqsext_gitlab.resolver.GitLabClient.get_issue"
        ) as mock_get:
            mock_get.return_value = mock_issue_data
            resolver = load_resolver_callback()

            with self.assertLogs("treqs-on-git.treqs-ng", level=10):
                le = list_elements(resolver_callback=resolver)
                returnCode = le.list_elements(
                    "tests/test_data/2-test-list-treq-elements.md",
                    treqs_type=None,
                    recursive=False,
                    uid="gl:my-project#42",
                    outlinks=False,
                    inlinks=False,
                )

            self.assertEqual(returnCode, 0)
            self.assertEqual(len(le.element_list), 1)

            # Verify the resolved external element
            ext_element = le.element_list[0]
            self.assertTrue(ext_element.is_external)
            self.assertEqual(ext_element.uid, "gl:my-project#42")
            self.assertEqual(ext_element.label, "External Issue #42")
            self.assertEqual(ext_element.treqs_type, "issue")
            self.assertEqual(
                ext_element.file_name,
                "https://gitlab.com/my-project/-/issues/42",
            )


if __name__ == "__main__":
    unittest.main()

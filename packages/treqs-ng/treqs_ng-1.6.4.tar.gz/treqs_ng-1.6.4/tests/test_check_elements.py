import io
import logging
import unittest
from pathlib import Path
from unittest.mock import patch

from treqs import main
from treqs.check_elements import check_elements
from treqs.treqs_element import treqs_element_factory

# Constants
CHECK_ELEMENTS_FILE = str(
    Path("./tests/test_data/5-test-faulty-types-and-links.md")
)
SUCCESSFUL_CHECK_ELEMENTS_FILE = str(
    Path("./tests/test_data/5-test-successful-check.md")
)
FAIL_FOR_MISSING_TTIM_FILE = str(
    Path("./tests/test_data/5-test-successful-check.md")
)
CHECK_LINKS_FILE = str(
    Path("./tests/test_data/7-test-faulty-inlinks-outlinks.md")
)
CHECK_DUPLICATE_IDS_FILE = str(Path("./tests/test_data/duplicate-ids"))
CHECK_DUPLICATE_ID_ONE_FILE = str(
    Path("tests/test_data/duplicate-ids/file_one.md")
)
CHECK_DUPLICATE_ID_TWO_FILE = str(
    Path("tests/test_data/duplicate-ids/file_two.md")
)
MULTIPLE_TARGETS_FILE = str(Path("./tests/test_data/multiple-targets.md"))

CHECK_NON_REQUIRED_OUTLINK_TTIM = str(
    Path("./tests/test_data/required/ttim.yaml")
)
CHECK_NON_REQUIRED_OUTLINK_REQS = str(
    Path("./tests/test_data/required/reqs.md")
)


class TestCheckElements(unittest.TestCase):
    # <treqs-element id="e9db9d24920d11eba831f018989356c1" type="unittest">
    # setup and successful checks of ./test_data/5-test-faulty-types-and-links.md
    # <treqs-link type="tests" target="3cff0d2a919511eb8becf018989356c1" />
    # <treqs-link type="tests" target="951ecc70919511eb978ff018989356c1" />
    # <treqs-link type="tests" target="a787f400223011ecb43ef018989356c1" />
    # <treqs-link type="tests" target="a787f3a6223011ecb43ef018989356c1" />
    # <treqs-link type="tests" target="a787f342223011ecb43ef018989356c1" />
    # <treqs-link type="tests" target="a787f20c223011ecb43ef018989356c1" />
    # </treqs-element>
    def test_check_elements(self):
        tef = treqs_element_factory()
        ce = check_elements(verbose=True, testing=True)
        success = ce.check_elements(CHECK_ELEMENTS_FILE, False, "./ttim.yaml")
        self.assertEqual(success, 1)
        self.assertEqual(1, ce.fileCount())

        # Check the amount of findings
        self.assertEqual(8, len(ce.uidWithFinding()))
        self.assertEqual(
            1, len(ce.findingsForUID("e770de36920911eb9355f018989356c1"))
        )
        self.assertEqual(
            1, len(ce.findingsForUID("2c600896920a11ebbb6ff018989356c1"))
        )
        self.assertEqual(
            1, len(ce.findingsForUID("56cbd2e0920a11ebb9d1f018989356c1"))
        )
        self.assertEqual(
            2, len(ce.findingsForUID("9d3a98c80bd711ec8e3ff018989356c1"))
        )
        self.assertEqual(
            1, len(ce.findingsForUID("4f5bcadad45711eb9de4f018989356c1"))
        )
        self.assertEqual(
            1, len(ce.findingsForUID("3cabd686d45811ebaaeef018989356c1"))
        )
        self.assertEqual(
            4, len(ce.findingsForUID("940f4d62920a11eba034f018989356c1"))
        )
        self.assertEqual(1, len(ce.findingsForUID("no valid id")))
        # Check the getter
        self.assertEqual(8, len(ce.getFindings()))

        # Check the messages
        self.assertEqual(
            "Element has an unrecognized type: 'non-existing-type'",
            ce.findingsForUID("e770de36920911eb9355f018989356c1")[0].message,
        )
        self.assertEqual(
            "Unrecognised outlink type relatesToo within element of type requirement.",
            ce.findingsForUID("2c600896920a11ebbb6ff018989356c1")[0].message,
        )
        self.assertEqual(
            "Unrecognised outlink type tests within element of type requirement.",
            ce.findingsForUID("56cbd2e0920a11ebb9d1f018989356c1")[0].message,
        )
        self.assertEqual(
            "Element has an unrecognized type: ''",
            ce.findingsForUID("9d3a98c80bd711ec8e3ff018989356c1")[0].message,
        )
        self.assertEqual(
            "Element has an empty or missing type.",
            ce.findingsForUID("9d3a98c80bd711ec8e3ff018989356c1")[1].message,
        )
        self.assertEqual(
            "Element references non-existent element with id 'inexistent_target_id'",
            ce.findingsForUID("4f5bcadad45711eb9de4f018989356c1")[0].message,
        )
        self.assertEqual(
            "``addresses`` link to element '4f5bcadad45711eb9de4f018989356c1' needs to point to a ``stakeholder-requirement``, but points to a ``requirement`` instead.",
            ce.findingsForUID("3cabd686d45811ebaaeef018989356c1")[0].message,
        )

        # For duplicated ID, we will also get an "inlink missing" finding for the second instance.
        self.assertEqual(
            "Required inlinks missing: ['tests']",
            ce.findingsForUID("940f4d62920a11eba034f018989356c1")[0].message,
        )
        self.assertEqual(
            34,
            ce.findingsForUID("940f4d62920a11eba034f018989356c1")[
                0
            ].element.placement,
        )
        # Non-existent element reference
        self.assertEqual(
            "Element references non-existent element with id 'None'",
            ce.findingsForUID("940f4d62920a11eba034f018989356c1")[1].message,
        )
        self.assertEqual(
            28,
            ce.findingsForUID("940f4d62920a11eba034f018989356c1")[
                1
            ].element.placement,
        )
        # For duplicated UI, make sure that we note both (or all) locations
        self.assertEqual(
            "Element id is duplicated.",
            ce.findingsForUID("940f4d62920a11eba034f018989356c1")[2].message,
        )
        self.assertEqual(
            34,
            ce.findingsForUID("940f4d62920a11eba034f018989356c1")[
                2
            ].element.placement,
        )
        self.assertEqual(
            "Element id is duplicated.",
            ce.findingsForUID("940f4d62920a11eba034f018989356c1")[3].message,
        )
        self.assertEqual(
            28,
            ce.findingsForUID("940f4d62920a11eba034f018989356c1")[
                3
            ].element.placement,
        )

        self.assertEqual(
            "Element does not have an id.",
            ce.findingsForUID("no valid id")[0].message,
        )

    # <treqs-element id="a813ac0c0bd811ecae3df018989356c1" type="unittest">
    # setup and successful checks of ./test_data/5-test-successful-check.md
    # <treqs-link type="tests" target="c5402c1a919411eb8311f018989356c1" />
    # </treqs-element>
    def test_successfully_check_elements(self):
        ce = check_elements(verbose=True, testing=True)
        success = ce.check_elements(
            SUCCESSFUL_CHECK_ELEMENTS_FILE, False, "./ttim.yaml"
        )

        self.assertEqual(success, 0)
        self.assertEqual(0, len(ce.getFindings()))

    # <treqs-element id="31ae24ac223011ec8859f018989356c1" type="unittest">
    # tests that treqs check fails when ttim is not found
    # <treqs-link type="tests" target="c5402c1a919411eb8311f018989356c1" />
    # <treqs-link type="tests" target="a787f400223011ecb43ef018989356c1" />
    # </treqs-element>
    def test_check_links(self):
        ce = check_elements(verbose=True, testing=True)
        success = ce.check_elements(CHECK_LINKS_FILE, False, "./ttim.yaml")

        self.assertEqual(success, 1)
        self.assertEqual(
            len(ce.findingsForUID("abeb5e8ce0b711ebaa057085c2221ca0")), 4
        )
        self.assertEqual(
            len(ce.findingsForUID("afca2be7e0b711eb9b8d7085c2221ca0")), 2
        )
        self.assertEqual(
            len(ce.findingsForUID("ae05cc8de0b711eb83b37085c2221ca0")), 2
        )
        self.assertEqual(
            ce.findingsForUID("abeb5e8ce0b711ebaa057085c2221ca0")[0].message,
            f"Required inlinks missing: ['tests']",
        )
        self.assertEqual(
            ce.findingsForUID("abeb5e8ce0b711ebaa057085c2221ca0")[1].message,
            f"Unrecognised outlink type NoType within element of type requirement.",
        )
        self.assertEqual(
            ce.findingsForUID("abeb5e8ce0b711ebaa057085c2221ca0")[2].message,
            f"Unrecognised outlink type WrongType within element of type requirement.",
        )
        self.assertEqual(
            ce.findingsForUID("abeb5e8ce0b711ebaa057085c2221ca0")[3].message,
            f"``hasParent`` link to element '48773577e0c611eb85447085c2221ca0' needs to point to a ``requirement``, but points to a ``stakeholder-requirement`` instead.",
        )
        self.assertEqual(
            ce.findingsForUID("ae05cc8de0b711eb83b37085c2221ca0")[0].message,
            f"``addresses`` link to element 'afca2be7e0b711eb9b8d7085c2221ca0' needs to point to a ``stakeholder-need``, but points to a ``unittest`` instead.",
        )
        self.assertEqual(
            ce.findingsForUID("ae05cc8de0b711eb83b37085c2221ca0")[1].message,
            f"``addresses`` link to element 'abeb5e8ce0b711ebaa057085c2221ca0' needs to point to a ``stakeholder-need``, but points to a ``requirement`` instead.",
        )

    # <treqs-element id="9282104204e311f0854a1c697aa14cc2" type="unittest">
    # Tests whether duplicate ids are found across multiple files.
    # <treqs-link target="c30a2aeadfaf11ef8751d89ef374263e" type ="tests"/>
    # <treqs-link target="a787f342223011ecb43ef018989356c1" type ="tests"/>
    # </treqs-element>
    def test_check_duplicate_ids_across_multiple_files(self):
        ce = check_elements(verbose=True, testing=True)
        success = ce.check_elements(
            CHECK_DUPLICATE_IDS_FILE, False, "./ttim.yaml"
        )
        self.assertEqual(success, 1)

        self.assertEqual(len(ce.uidWithFinding()), 1)
        self.assertEqual(ce.fileCount(), 2)

        self.assertEqual(len(ce.findingsForUID("a-very-unique-id")), 3)
        self.assertEqual(
            ce.findingsForUID("a-very-unique-id")[0].message,
            "Element id is duplicated.",
        )
        self.assertEqual(
            ce.findingsForUID("a-very-unique-id")[0].element.file_name,
            CHECK_DUPLICATE_ID_ONE_FILE,
        )
        self.assertEqual(
            ce.findingsForUID("a-very-unique-id")[0].element.placement, 6
        )
        self.assertEqual(
            ce.findingsForUID("a-very-unique-id")[1].element.file_name,
            CHECK_DUPLICATE_ID_ONE_FILE,
        )
        self.assertEqual(
            ce.findingsForUID("a-very-unique-id")[1].element.placement, 1
        )
        self.assertEqual(
            ce.findingsForUID("a-very-unique-id")[1].message,
            "Element id is duplicated.",
        )
        self.assertEqual(
            ce.findingsForUID("a-very-unique-id")[2].element.file_name,
            CHECK_DUPLICATE_ID_TWO_FILE,
        )
        self.assertEqual(
            ce.findingsForUID("a-very-unique-id")[2].element.placement, 1
        )
        self.assertEqual(
            ce.findingsForUID("a-very-unique-id")[2].message,
            "Element id is duplicated.",
        )

    # <treqs-element id="3bd1feb262a311ee98f915f1b0e25002" type="unittest">
    # tests that treqs check accepts and processes links with multiple target types
    # <treqs-link type="tests" target="d00b0858628a11ee98f915f1b0e25002" />
    # <treqs-link type="tests" target="a0ae1162a72711ef80988adebfb72d7c" />
    # </treqs-element>
    def test_multiple_targets(self):
        ce = check_elements(verbose=True, testing=True)
        success = ce.check_elements(
            MULTIPLE_TARGETS_FILE,
            False,
            "./tests/test_data/multiple-targets-ttim.yaml",
        )
        self.assertEqual(success, 1)
        self.assertEqual(2, len(ce.getFindings()))
        uids = list(ce.uidWithFinding())
        self.assertEqual(2, len(uids))
        self.assertEqual(uids[0], "a")
        self.assertEqual(uids[1], "b")

        aFind = ce.findingsForUID("a")
        bFind = ce.findingsForUID("b")
        self.assertEqual(1, len(aFind))
        self.assertEqual(1, len(bFind))

        self.assertEqual(
            aFind[0].message,
            "``relatesTo`` link to element 'a' needs to point to one of these ``['B', 'C']``, but points to a ``A`` instead.",
        )
        self.assertEqual(aFind[0].element.uid, "a")
        self.assertEqual(
            bFind[0].message,
            "``relatesTo`` link to element 'a' needs to point to a ``C``, but points to a ``A`` instead.",
        )
        self.assertEqual(bFind[0].element.uid, "b")

    # <treqs-element id="72b6a098dc634be38d30d5c0614c7852" type="unittest">
    # Test whether typical configuration errors in ttim yield warnings rather than exceptions.
    # <treqs-link type="tests" target="a0ae1162a72711ef80988adebfb72d7c" />
    # </treqs-element>
    def test_ttim_error_robustness(self):
        ce = check_elements(verbose=True, testing=True)
        success = ce.check_elements(
            MULTIPLE_TARGETS_FILE,
            False,
            "./tests/test_data/broken-ttim-1.yaml",
        )
        self.assertEqual(success, 1)
        self.assertEqual(3, len(ce.getFindings()))
        uids = list(ce.uidWithFinding())
        self.assertEqual(3, len(uids))
        self.assertEqual(uids[0], "a")
        self.assertEqual(uids[1], "b")
        self.assertEqual(uids[2], "c")

        aFind = ce.findingsForUID("a")
        bFind = ce.findingsForUID("b")
        cFind = ce.findingsForUID("c")
        self.assertEqual(4, len(aFind))
        self.assertEqual(1, len(bFind))
        self.assertEqual(1, len(cFind))

        self.assertEqual(
            aFind[0].message,
            "Unrecognised inlink type relatesTo within element of type A.",
        )
        self.assertEqual(
            aFind[1].message,
            "Unrecognised outlink type relatesTo within element of type A.",
        )
        self.assertEqual(
            aFind[2].message,
            "Unrecognised outlink type relatesTo within element of type A.",
        )
        self.assertEqual(
            aFind[3].message,
            "Unrecognised outlink type relatesTo within element of type A.",
        )
        self.assertEqual(aFind[0].element.uid, "a")
        self.assertEqual(
            bFind[0].message,
            "Unrecognised inlink type relatesTo within element of type B.",
        )
        self.assertEqual(bFind[0].element.uid, "b")
        self.assertEqual(
            cFind[0].message,
            "Unrecognised inlink type relatesTo within element of type C.",
        )
        self.assertEqual(cFind[0].element.uid, "c")

    # <treqs-element id="a3e277bc55d511f0ba248adebfb72d7e" type="unittest">
    # Test if required inlinks are present.
    # <treqs-link type="tests" target="a0ae1162a72711ef80988adebfb72d7c" />
    # <treqs-link type="tests" target="b4d30bec919711eba4e1f018989356c1" />
    # </treqs-element>
    def test_inlinks_check(self):
        """Test that required incoming links are properly checked."""
        test_file = Path("tests/test_data/inlinks-check/simple.md")
        ttim_file = Path("tests/test_data/inlinks-check/ttim.yaml")

        # Run check
        checker = check_elements(verbose=True, testing=True)
        result = checker.check_elements(
            file_name=test_file,
            recursive=True,
            ttim_path=str(ttim_file),
        )

        # Get findings
        findings = checker.getFindings()

        # Verify results
        self.assertEqual(result, 1, "Check should fail due to missing inlink")
        self.assertIn("REQ-1", findings, "REQ-1 should have findings")
        self.assertNotIn("REQ-2", findings, "REQ-2 should not have findings")

        # Verify specific error message
        req1_findings = findings.get("REQ-1", [])
        self.assertTrue(
            any(
                "Required inlinks missing: ['implements']" in f.message
                for f in req1_findings
            ),
            "Should report missing implements link",
        )

    # <treqs-element id="24758c36574b11f090af8adebfb72d7e" type="unittest">
    # Test advanced link scenarios related to inlinks.
    # <treqs-link type="tests" target="b2c9f8d2dfb111ef9c8dd89ef374263e" />
    # <treqs-link type="tests" target="a0ae1162a72711ef80988adebfb72d7c" />
    # <treqs-link type="tests" target="b4d30bec919711eba4e1f018989356c1" />
    # </treqs-element>
    def test_link_scenarios(self):
        """Test various link configurations defined in TTIM."""
        test_file = Path("tests/test_data/inlinks-check/advanced.md")
        ttim_file = Path("tests/test_data/inlinks-check/ttim.yaml")

        # Run check
        checker = check_elements(verbose=True, testing=True)
        result = checker.check_elements(
            str(test_file), recursive=False, ttim_path=str(ttim_file)
        )

        findings = checker.getFindings()

        # Test requirement with implementation
        self.assertNotIn(
            "REQ-1",
            findings,
            "REQ-1 should pass as it has required implementation",
        )

        # Test implementation with valid outlink
        self.assertNotIn(
            "IMPL-1",
            findings,
            "IMPL-1 should pass as implements link is valid",
        )

        # Test feature with only outlinks defined
        self.assertNotIn(
            "FEAT-1",
            findings,
            "FEAT-1 should pass as it only needs outlinks defined",
        )

        # Test test case requiring inlinks
        self.assertIn(
            "TEST-1",
            findings,
            "TEST-1 should fail as it requires verification",
        )
        test_findings = findings.get("TEST-1", [])
        self.assertTrue(
            any(
                "Required inlinks missing: ['verifies']" in f.message
                for f in test_findings
            ),
            "Should report missing verifies link for TEST-1",
        )

        # Test note with no link definitions
        self.assertNotIn(
            "NOTE-1",
            findings,
            "NOTE-1 should pass as it has no link requirements",
        )

        # Verify overall result
        self.assertEqual(
            result, 1, "Check should fail due to missing required inlinks"
        )

    # <treqs-element id="d2bd4dc25e7d11f08a3716273c619a7a" type="unittest">
    # <treqs-link type="tests" target="b4d30bec919711eba4e1f018989356c1" />
    # <treqs-link type="tests" target="b2c9f8d2dfb111ef9c8dd89ef374263e" />
    # </treqs-element>
    def test_non_required_outlink(self):
        with self.assertRaises(SystemExit) as cm:
            main.check(
                [
                    "--ttim",
                    CHECK_NON_REQUIRED_OUTLINK_TTIM,
                    CHECK_NON_REQUIRED_OUTLINK_REQS,
                ]
            )
        self.assertEqual(cm.exception.code, 0)

    def setUp(self):
        # initialise logger
        logger = logging.getLogger("treqs-on-git.treqs-ng")
        # We use level 10 for debug, level 20 for verbose, level 30 and higher for important
        # This corresponds to the macros 10 for DEBUG, 20 for INFO, and 30 for WARNING, but has different semantics
        logger.setLevel(100)
        console_handler = logging.StreamHandler()
        # NOTE: We could have different levels for different handlers as well.
        # console_handler.setLevel(10)
        # only display message for now.
        formatter = logging.Formatter("%(message)s")
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        return super().setUp()

    # <treqs-element id="478966ca55d411f09bbd8adebfb72d7e" type="unittest">
    # Test checking an individual file without and with problems.
    # <treqs-link type="tests" target="e76995c4509c11edbe22c9328ceec9a7" />
    # <treqs-link type="tests" target="8cedc2a5509d11edbe22c9328ceec9a7" />
    # <treqs-link type="tests" target="a0ae1162a72711ef80988adebfb72d7c" />
    # <treqs-link type="tests" target="7ffb9ea8dfaf11ef9d72d89ef374263e" />
    # </treqs-element>
    def test_check_exit_code(self):
        # Succesful case (no failed checks)
        fake_out = io.StringIO()
        with patch("sys.stdout", new=fake_out):
            with self.assertRaises(SystemExit) as cm:
                main.check(
                    [
                        "--recursive",
                        "False",
                        "--ttim",
                        "./ttim.yaml",
                        "--verbose",
                        SUCCESSFUL_CHECK_ELEMENTS_FILE,
                    ]
                )
        captured = fake_out.getvalue().splitlines()
        self.assertEqual(cm.exception.code, 0)
        self.assertEqual(len(captured), 14)
        self.assertEqual(captured[0], "Loaded resolver 'gl' from extension")
        self.assertEqual(captured[1], "file_traverser created")
        self.assertEqual(captured[2], "treqs_element_factory created")
        self.assertEqual(captured[3], "list_elements created")
        self.assertEqual(captured[4], "check_elements created")
        self.assertEqual(captured[5], "Processing TTIM at ./ttim.yaml")
        # Since this test relies on the productive TTIM, best to not ask for details.
        self.assertTrue("TTIM Configuration:" in captured[6])
        self.assertTrue("Outlinks:" in captured[7])
        self.assertTrue("Inlinks:" in captured[8])
        self.assertEqual(
            captured[11],
            f"Calling XML traversal with filename {SUCCESSFUL_CHECK_ELEMENTS_FILE}",
        )
        self.assertEqual(
            captured[12],
            f"   ### Processing elements in File {SUCCESSFUL_CHECK_ELEMENTS_FILE}",
        )
        self.assertRegex(
            captured[13],
            "treqs check: checked 1 files .0 files ignored, 0 files unreadable, 0 files corrupt. in ....s. OK.",
        )

        # Failed checks
        with patch("sys.stdout", new=fake_out):
            with self.assertRaises(SystemExit) as cm:
                main.check(
                    [
                        "--recursive",
                        "False",
                        CHECK_ELEMENTS_FILE,
                        "--ttim",
                        "./ttim.yaml",
                        "--verbose",
                    ]
                )
        captured = fake_out.getvalue().splitlines()
        self.assertEqual(cm.exception.code, 1)
        self.assertEqual(len(captured), 42)
        self.assertEqual(captured[0], "Loaded resolver 'gl' from extension")
        self.assertEqual(captured[1], "file_traverser created")
        self.assertEqual(captured[2], "treqs_element_factory created")
        self.assertEqual(captured[3], "list_elements created")
        self.assertEqual(captured[4], "check_elements created")
        self.assertEqual(captured[5], "Processing TTIM at ./ttim.yaml")
        self.assertTrue("TTIM Configuration:" in captured[6])
        self.assertTrue("Outlinks:" in captured[7])
        self.assertTrue("Inlinks:" in captured[8])
        self.assertTrue(
            f"Calling XML traversal with filename {CHECK_ELEMENTS_FILE}"
            in captured,
        )
        self.assertTrue(
            f"   ### Processing elements in File {CHECK_ELEMENTS_FILE}"
            in captured
        )
        self.assertTrue("| Error location | Error | File:Line |" in captured)
        self.assertTrue("| :--- | :--- | :--- |" in captured)
        self.assertTrue(
            f"| Element e770de36920911eb9355f018989356c1 | Element has an unrecognized type: 'non-existing-type' | {CHECK_ELEMENTS_FILE}:1 |"
            in captured
        )
        self.assertTrue(
            f"| Element 2c600896920a11ebbb6ff018989356c1 | Unrecognised outlink type relatesToo within element of type requirement. | {CHECK_ELEMENTS_FILE}:8 |"
            in captured
        )
        self.assertTrue(
            f"| Element 56cbd2e0920a11ebb9d1f018989356c1 | Unrecognised outlink type tests within element of type requirement. | {CHECK_ELEMENTS_FILE}:15 |"
            in captured
        )
        self.assertTrue(
            f"| Element 9d3a98c80bd711ec8e3ff018989356c1 | Element has an unrecognized type: '' | {CHECK_ELEMENTS_FILE}:57 |"
            in captured
        )
        self.assertTrue(
            f"| Element 9d3a98c80bd711ec8e3ff018989356c1 | Element has an empty or missing type. | {CHECK_ELEMENTS_FILE}:57 |"
            in captured
        )
        self.assertTrue(
            f"| Element 4f5bcadad45711eb9de4f018989356c1 | Element references non-existent element with id 'inexistent_target_id' | {CHECK_ELEMENTS_FILE}:44 |"
            in captured
        )
        self.assertTrue(
            f"| Element 3cabd686d45811ebaaeef018989356c1 | ``addresses`` link to element '4f5bcadad45711eb9de4f018989356c1' needs to point to a ``stakeholder-requirement``, but points to a ``requirement`` instead. | {CHECK_ELEMENTS_FILE}:50 |"
            in captured
        )
        self.assertTrue(
            f"| Element 940f4d62920a11eba034f018989356c1 | Element id is duplicated. | {CHECK_ELEMENTS_FILE}:34 |"
            in captured
        )
        self.assertTrue(
            f"| Element 940f4d62920a11eba034f018989356c1 | Element id is duplicated. | {CHECK_ELEMENTS_FILE}:28 |"
            in captured
        )
        self.assertTrue(
            f"| Element None | Element does not have an id. | {CHECK_ELEMENTS_FILE}:22 |"
            in captured
        )
        print(captured[-1])
        self.assertRegex(
            captured[-1],
            r"treqs check: checked \d+ files in \d+\.\d+s\. Exited with \d+ failed checks\.",
        )

    # <treqs-element id="fec54ee40c0411eca67ff018989356c1" type="unittest">
    # tests that treqs check fails when ttim is not found
    # <treqs-link type="tests" target="a0ae1162a72711ef80988adebfb72d7c" />
    # <treqs-link type="tests" target="c5402c1a919411eb8311f018989356c1" />
    # </treqs-element>
    def test_fail_for_missing_ttim(self):
        fake_out = io.StringIO()
        with patch("sys.stdout", new=fake_out):
            with self.assertRaises(SystemExit) as cm:
                main.check(
                    [
                        "--recursive",
                        "False",
                        FAIL_FOR_MISSING_TTIM_FILE,
                        "--ttim",
                        "./ttim_missing.yaml",
                        "--verbose",
                    ]
                )
        captured = fake_out.getvalue().splitlines()
        self.assertEqual(cm.exception.code, 1)
        self.assertEqual(len(captured), 8)
        self.assertTrue("Loaded resolver 'gl' from extension" in captured)
        self.assertTrue("file_traverser created" in captured)
        self.assertTrue("treqs_element_factory created" in captured)
        self.assertTrue("list_elements created" in captured)
        self.assertTrue("check_elements created" in captured)
        self.assertTrue("Processing TTIM at ./ttim_missing.yaml" in captured)
        self.assertTrue(
            "TTIM could not be loaded at ./ttim_missing.yaml" in captured
        )
        self.assertRegex(
            captured[-1],
            r"^treqs check: checked \d+ files in \d+\.\d+s\. Exited with \d+ failed checks\.$",
        )


if __name__ == "__main__":
    unittest.main()

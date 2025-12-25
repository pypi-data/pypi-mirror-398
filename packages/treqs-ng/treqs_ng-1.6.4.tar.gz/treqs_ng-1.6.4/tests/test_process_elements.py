import logging
import unittest
import os

from treqs.process_elements import process_elements


class TestProcessElements(unittest.TestCase):
    def setUp(self):
        self.pe = process_elements()
        self.cwd = os.getcwd()
        # initialise logger
        logger = logging.getLogger("treqs-on-git.treqs-ng")
        # We use level 10 for debug, level 20 for verbose, level 30 and higher for important
        # This corresponds to the macros 10 for DEBUG, 20 for INFO, and 30 for WARNING, but has different semantics
        logger.setLevel(100)
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter("%(message)s")
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        return super().setUp()

    # test that gen folder can be created
    def test_create_gen_dir(self):
        self.pe.create_gen_dir()
        self.assertEqual(os.path.exists(os.getcwd() + "/gen"), True)

    # <treqs-element id="aec9386489c911eb99c7c4b301c00591" type="unittest">
    # Test that a plantuml block is correctly processed and replaced by an image link
    # <treqs-link type="tests" target="9a8a627687f111eb9d1ec4b301c00591" />
    # <treqs-link type="tests" target="c153f342220e11eca165f018989356c1" />
    # </treqs-element>
    def test_create_plantuml_links_no_codeblock(self):
        lines = []
        lines.append("@startuml test_diagram\n")
        lines.append("crazy plantUML content\n")
        lines.append("@enduml\n")
        lines.append("\n")
        self.assertEqual(4, len(lines))
        newlines, diagram_names = self.pe.create_plantuml_links(lines)
        self.assertEqual(2, len(newlines))
        self.assertEqual("![test_diagram](test_diagram.png)\n", newlines[0])
        self.assertEqual("\n", newlines[1])
        self.assertEqual("test_diagram", diagram_names[0])

    # <treqs-element id="26e73f34220f11ec9a49f018989356c1" type="unittest">
    # Test that a plantuml block in multi-line code block is correctly processed and an image link is added.
    # <treqs-link type="tests" target="c153021087f011eb8a15c4b301c00591" />
    # <treqs-link type="tests" target="9a8a627687f111eb9d1ec4b301c00591" />
    # </treqs-element>
    def test_create_plantuml_links_codeblock(self):
        lines = []
        lines.append("```")
        lines.append("@startuml test_diagram\n")
        lines.append("crazy plantUML content\n")
        lines.append("@enduml\n")
        lines.append("```")
        lines.append("\n")
        self.assertEqual(6, len(lines))
        newlines, diagram_names = self.pe.create_plantuml_links(lines)
        self.assertEqual(7, len(newlines))
        self.assertEqual("```", newlines[0])
        self.assertEqual("@startuml test_diagram\n", newlines[1])
        self.assertEqual("crazy plantUML content\n", newlines[2])
        self.assertEqual("@enduml\n", newlines[3])
        self.assertEqual("```", newlines[4])
        self.assertEqual("![test_diagram](test_diagram.png)\n", newlines[5])
        self.assertEqual("\n", newlines[6])
        self.assertEqual("test_diagram", diagram_names[0])

    # <treqs-element id="d2f361f2221111ec8700f018989356c1" type="unittest">
    # Test that no additional image links are generated, if they are already there.
    # <treqs-link type="tests" target="9df5647c220d11eca690f018989356c1" />
    # </treqs-element>
    def test_create_plantuml_links_existing_imagelink(self):
        lines = []
        lines.append("```")
        lines.append("@startuml test_diagram\n")
        lines.append("crazy plantUML content\n")
        lines.append("@enduml\n")
        lines.append("```")
        lines.append("![test_diagram](test_diagram.png)\n")
        lines.append("\n")
        self.assertEqual(7, len(lines))
        newlines, diagram_names = self.pe.create_plantuml_links(lines)
        self.assertEqual(7, len(newlines))
        self.assertEqual("```", newlines[0])
        self.assertEqual("@startuml test_diagram\n", newlines[1])
        self.assertEqual("crazy plantUML content\n", newlines[2])
        self.assertEqual("@enduml\n", newlines[3])
        self.assertEqual("```", newlines[4])
        self.assertEqual("![test_diagram](test_diagram.png)\n", newlines[5])
        self.assertEqual("\n", newlines[6])
        self.assertEqual("test_diagram", diagram_names[0])

    # Check that treqs process does not fail even if the diagram name is not given
    def test_create_unnamed_plantuml_links(self):
        lines = []
        lines.append("@startuml\n")
        lines.append("crazy plantUML content\n")
        lines.append("@enduml\n")
        lines.append("\n")
        self.assertEqual(4, len(lines))
        newlines, diagram_names = self.pe.create_plantuml_links(lines)
        self.assertEqual(2, len(newlines))
        self.assertEqual("![untitled](untitled.png)\n", newlines[0])
        self.assertEqual("\n", newlines[1])
        self.assertEqual("untitled", diagram_names[0])

    def tearDown(self):
        if os.path.exists("test.md"):
            os.remove("test.md")
        if os.path.exists(os.getcwd() + "/gen/process_plantuml.png"):
            os.remove(os.getcwd() + "/gen/process_plantuml.png")
        if os.path.exists(os.getcwd() + "/gen/Sample.png"):
            os.remove(os.getcwd() + "/gen/Sample.png")
        if os.path.exists(os.getcwd() + "/gen/process_plantuml.cmapx"):
            os.remove(os.getcwd() + "/gen/process_plantuml.cmapx")
        if os.path.exists(os.getcwd() + "/gen"):
            os.rmdir(os.getcwd() + "/gen")


if __name__ == "__main__":
    unittest.main()

import os
import subprocess
import unittest

from treqs.process_elements import process_elements


class TestProcessElements(unittest.TestCase):
    def setUp(self):
        self.pe = process_elements()
        self.cwd = os.getcwd()

    @classmethod
    def setUpClass(cls):
        if os.path.exists("test.md"):
            os.remove("test.md")
        if os.path.exists(os.getcwd() + "/gen/example.md"):
            os.remove(os.getcwd() + "/gen/example.md")
        if os.path.exists(os.getcwd() + "/gen/test_diagram.png"):
            os.remove(os.getcwd() + "/gen/test_diagram.png")
        if os.path.exists(os.getcwd() + "/gen/process_plantuml.svg"):
            os.remove(os.getcwd() + "/gen/process_plantuml.svg")
        if os.path.exists(os.getcwd() + "/gen/Sample.svg"):
            os.remove(os.getcwd() + "/gen/Sample.svg")
        if os.path.exists(os.getcwd() + "/gen/process_plantuml.png"):
            os.remove(os.getcwd() + "/gen/process_plantuml.png")
        if os.path.exists(os.getcwd() + "/gen/Sample.png"):
            os.remove(os.getcwd() + "/gen/Sample.png")
        if os.path.exists(os.getcwd() + "/gen/process_plantuml.html"):
            os.remove(os.getcwd() + "/gen/process_plantuml.html")
        if os.path.exists(os.getcwd() + "/gen/Sample.html"):
            os.remove(os.getcwd() + "/gen/Sample.html")
        if os.path.exists(os.getcwd() + "/gen/process_plantuml.cmapx"):
            os.remove(os.getcwd() + "/gen/process_plantuml.cmapx")
        if os.path.exists(os.getcwd() + "/gen"):
            os.rmdir(os.getcwd() + "/gen")

    # Tests that gen folder can be and is created by the respective functon.
    def test_create_gen_dir(self):
        self.pe.create_gen_dir()
        self.assertEqual(os.path.exists(os.getcwd() + "/gen"), True)

    # Test that plantuml execution works on a file that exclusively contains a single plantuml block.
    def test_make_plantuml_figures(self):
        lines = []
        lines.append("<treqs>\n")
        lines.append("@startuml test_diagram\n")
        lines.append("Alice -> Bob\n")
        lines.append("@enduml\n")
        lines.append("</treqs>\n")
        lines.append("\n")
        with open("test.md", "w+") as md:
            md.writelines(lines)
        self.assertEqual(os.path.exists(self.cwd + "/test.md"), True)
        self.pe.make_plantuml_figures("test.md")
        self.assertEqual(os.path.exists("gen/test_diagram.png"), True)

    # <treqs-element id="4ac31fa6221211ec9657f018989356c1" type="unittest">
    # An integration test checking that process_elements creates all the right images.
    # <treqs-link type="tests" target="c153021087f011eb8a15c4b301c00591" />
    # <treqs-link type="tests" target="9a8a627687f111eb9d1ec4b301c00591" />
    # </treqs-element>
    def test_integration_process_elements(self):
        """Tests the entire chain from calling process_elements"""

        with self.assertLogs("treqs-on-git.treqs-ng", level=10) as captured:
            self.pe.process_elements(
                "tests/test_data/example.md", False, False, False
            )

        self.assertEqual(
            os.path.exists(self.cwd + "/gen/process_plantuml.svg"), False
        )
        self.assertEqual(os.path.exists(self.cwd + "/gen/Sample.svg"), False)
        self.assertEqual(
            os.path.exists(self.cwd + "/gen/process_plantuml.png"), True
        )
        self.assertEqual(os.path.exists(self.cwd + "/gen/Sample.png"), True)
        self.assertEqual(os.path.exists(self.cwd + "/gen/Sample.html"), False)
        self.assertEqual(
            os.path.exists(self.cwd + "/gen/process_plantuml.html"), False
        )
        self.assertEqual(os.path.exists(os.getcwd() + "/gen/example.md"), True)

        self.assertEqual(len(captured.records), 14)
        self.assertEqual(
            captured.records[0].getMessage(),
            "Cannot import treqs extensions. Falling back to core treqs process functionality.",
        )
        self.assertEqual(
            captured.records[1].getMessage(), "process_plantuml started"
        )
        self.assertEqual(
            captured.records[2].getMessage(),
            "Choosing generic traversal strategy",
        )
        self.assertEqual(
            captured.records[3].getMessage(),
            "   ### Processing elements in File tests/test_data/example.md",
        )
        self.assertEqual(
            captured.records[4].getMessage(),
            "Creating /gen directory at " + os.getcwd() + "/gen",
        )
        self.assertEqual(
            True,
            captured.records[5]
            .getMessage()
            .startswith("   Using plantuml binary at "),
        )
        self.assertEqual(captured.records[6].getMessage(), "\n   Generated")
        self.assertEqual(captured.records[7].getMessage(), "    Sample.png")
        self.assertEqual(
            captured.records[8].getMessage(),
            "Adding line: ![Sample](Sample.png)\n",
        )
        self.assertEqual(
            captured.records[9].getMessage(), "    process_plantuml.png"
        )
        self.assertEqual(
            captured.records[10].getMessage(),
            "Adding line: ![process_plantuml](process_plantuml.png)\n",
        )
        self.assertEqual(captured.records[11].getMessage(), "   Created")
        self.assertEqual(captured.records[12].getMessage(), "    example.md")
        self.assertEqual(
            captured.records[13].getMessage(),
            "   at " + os.getcwd() + "/gen\n",
        )

    # <treqs-element id="e63f02a255ac11f09acf8adebfb72d7e" type="unittest">
    # Tests whether the plantuml.jar in the local libs folder is MIT licensed.
    # <treqs-link type="tests" target="8793c8ca96eb11ebaca5c4b301c00591"/>
    # <treqs-link type="tests" target="c7e7946a96eb11ebbfd9c4b301c00591"/>
    # </treqs-element>
    def test_mit_license(self):
        libdir = os.path.split(__file__)[0] + "/../lib/plantuml.jar"

        result = subprocess.run(
            ["java", "-jar", libdir, "-version"], stdout=subprocess.PIPE
        )
        self.assertTrue("MIT source distribution" in str(result.stdout))

    def tearDown(self):
        if os.path.exists("test.md"):
            os.remove("test.md")
        if os.path.exists(os.getcwd() + "/gen/example.md"):
            os.remove(os.getcwd() + "/gen/example.md")
        if os.path.exists(os.getcwd() + "/gen/test_diagram.png"):
            os.remove(os.getcwd() + "/gen/test_diagram.png")
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

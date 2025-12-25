import logging
import os

from treqs.file_traverser import file_traverser

# Logger messages
LOG_EXT_FOUND = (
    # fmt: skip
    "Treqs extensions found. Using advanced treqs process functionality."
)
LOG_EXT_MISSING = (
    "Cannot import treqs extensions. "
    # fmt: skip
    "Falling back to core treqs process functionality."
)


class process_elements:
    def __init__(self):
        self.__logger = logging.getLogger("treqs-on-git.treqs-ng")
        self.traverser = file_traverser()
        self.__logger.log(10, "process_elements created")

    def process_elements(
        self,
        file_name,
        recursive=True,
        wbs=False,
        html=False,
        svg=False,
        links=False,
    ):
        """
        This method serves as an entry point for processing elements.
        It checks through a conditional import whether the treqs extensions
        module is installed.
        If that's the case, processing is delegated to the extensions.
        If not, the basic PlantUML generation based on the standalone jar file
        is executed.
        """
        try:
            from treqsext import advanced_processor

            self.__logger.log(
                10,
                LOG_EXT_FOUND,
            )
            self.processor = advanced_processor.advanced_processor()
            self.processor.process_elements(
                file_name,
                recursive,
                wbs,
                html,
                svg,
                links,
            )
        except ImportError:
            self.__logger.log(
                10,
                LOG_EXT_MISSING,
            )
            self.process_plantuml(file_name, recursive)

    def process_plantuml(self, file_name, recursive):
        self.__logger.log(10, "process_plantuml started")
        self.traverser.traverse_file_hierarchy(
            file_name,
            recursive,
            self.process_plantuml_file,
        )

    def process_plantuml_file(self, filename):
        self.make_plantuml_figures(filename)
        self.generate_markdown_file(filename)

    def make_plantuml_figures(self, filename):
        """
        Go through the file and create PNG files for each plantuml diagram.
        """
        self.create_gen_dir()
        libdir = os.path.split(__file__)[0] + "/../lib/plantuml.jar"
        self.__logger.log(10, "   Using plantuml binary at %s", libdir)
        os.system(
            "java -jar %s -tpng -o %s %s"
            % (
                libdir,
                os.getcwd() + "/gen/",
                filename,
            ),
        )

    def create_gen_dir(self):
        """Creates a /gen directory if not exists."""
        path = os.getcwd() + "/gen"
        if not os.path.exists(path):
            try:
                os.mkdir(path)
            except OSError:
                self.__logger.log(
                    40,
                    "Failed in creating /gen directory at %s" % path,
                )
            else:
                self.__logger.log(
                    10,
                    "Creating /gen directory at %s" % path,
                )

    def generate_markdown_file(self, filename):
        """
        Go through file, read into list and replace each plantUML block
        with link to the generated
        PNG file. Write result into new file in gen/.
        """
        try:
            with open(filename) as f:
                newlines, diagram_names = self.create_plantuml_links(
                    f.readlines(),
                )

            # Now, we create a new .md file for the generated markdown
            filename = filename.split("/")[-1]
            self.__logger.log(10, "   Created")
            self.__logger.log(10, "    %s" % filename)
            with open(os.getcwd() + "/gen/" + filename, "w+") as f:
                f.writelines(newlines)

            self.__logger.log(10, "   at %s/gen\n" % os.getcwd())
        except UnicodeDecodeError:
            self.__logger.log(40, "Error while decoding %s" % filename)

    def create_plantuml_links(self, lines):
        """
        Reads every line of a file into a list. If a block of plantUML code
        is found, the code block is replaced by an image reference.
        """
        newlines = []
        diagram_names = []
        reachedEnd = False
        reached_UML = False
        is_comment = False
        self.__logger.log(10, "\n   Generated")
        for index, line in enumerate(lines):
            # Are we currently in a markdown comment block?
            if line.startswith("```"):
                is_comment = not is_comment

                if reachedEnd:
                    # last line ended a uml block
                    picref = "![%s](%s.png)\n" % (name, name)
                    diagram_names.append(name)

                    # As we are in a code block, we add the image link
                    # afterwards.
                    # Skip if the reference is already there.
                    if not (
                        # fmt: skip
                        len(lines) > index + 1 and lines[index + 1] == picref
                    ):
                        self.__logger.log(10, "Adding line: %s", picref)
                        newlines.append(line)
                        line = picref
            elif reachedEnd:
                # last line ended a uml block
                picref = "![%s](%s.png)\n" % (name, name)
                diagram_names.append(name)

                # If we are not in a comment block, then we can just have the
                # reference in place
                if line != picref:
                    self.__logger.log(10, "Adding line: %s", picref)
                    newlines.append(picref)

            if reachedEnd:
                # This is cleanup for following plantuml blocks
                reachedEnd = False
                reached_UML = False

            # If a plantuml block is starting, we keep track of this.
            # Also, we extract the diagram name or 'untitled'.
            if line.startswith("@start"):
                reached_UML = True
                try:
                    name = line.split(" ", 1)[1].replace("\n", "")
                    self.__logger.log(10, "    %s.png", name)
                except IndexError:
                    self.__logger.log(20, "Untitled plantUML diagram")
                    name = "untitled"

            # If a plantuml block is not within comments, it will be replaced
            # by the image. Otherwise, we just keep the markdown content.
            if not (reached_UML and not is_comment):
                newlines.append(line)

            # have we reached the end of a plantuml block?
            reachedEnd = line.startswith("@end")

        # self.__logger.log(
        #    10,
        #    "Old lines: %i, new lines %i",
        #    len(lines),
        #    len(newlines),
        # )
        return newlines, diagram_names

import glob
import logging
import os
from xml.sax.saxutils import escape

from lxml import etree as ET

# Logger messages
LOG_CREATED = "file_traverser created"
LOG_IGNORE = "   ### Ignoring file %s (.treqs-ignore)"
LOG_SKIP_DIR = "\n\n### Non-recursive file_traverser, skipping directory %s"
LOG_NO_FILE = "\n\n### File or directory %s does not exist. Skipping."
LOG_XML = "\n\nCalling XML traversal with filename %s"
LOG_PROCESS = "   ### Processing elements in File %s"
LOG_PARSE_ERR = "   ### Skipping elements in File %s due to parser error (%s)"
LOG_DEC_ERR = "   ### Skipping elements in File %s due to UnicodeDecodeError"
LOG_GEN_ERR = "   ### Skipping elements in File %s due to: %s"
LOG_STRATEGY = "Choosing generic traversal strategy"


class file_traverser:
    def __init__(self, ignore_root="."):
        self.__logger = logging.getLogger("treqs-on-git.treqs-ng")
        self.__logger.log(10, LOG_CREATED)
        self.compiled_recursive_ignore_list = set()
        self.compiled_non_recursive_ignore_list = set()
        self.filecount = 0
        self.ignoredFileCount = 0
        self.unreadableFileCount = 0
        self.corruptFileCount = 0
        # Initialize ignore lists for root directory
        self.update_ignore_lists(ignore_root)

    def update_ignore_lists(self, directory):
        """Updates ignore lists by parsing .treqs-ignore
        in the given directory"""
        ignore_file = os.path.join(directory, ".treqs-ignore")
        patterns = self.import_treqs_ignore(ignore_file)

        # Convert patterns to absolute paths relative to
        # the ignore file's directory
        for pattern in patterns:
            glob_pattern = os.path.join(directory, pattern)
            # Add to recursive list
            for f in glob.glob(glob_pattern, recursive=True):
                self.compiled_recursive_ignore_list.add(os.path.normpath(f))
            # Add to non-recursive list (only current directory)
            for f in glob.glob(glob_pattern, recursive=False):
                self.compiled_non_recursive_ignore_list.add(
                    os.path.normpath(f)
                )

    def traverse_file_hierarchy(
        self,
        path,
        recursive,
        handler,
        traversal_strategy="",
        element_selector="",
    ):
        """
        Iterates over all files in a given directory (potentially recursive).
        For each file, the provided handler function is called
        """
        success = 0

        # A specific traversal strategy function can be provided.
        # If none is provided, call the generic one
        # (calling the handler for each file with a file name attribute)
        if traversal_strategy == "":
            self.__logger.log(10, LOG_STRATEGY)
            traversal_strategy = self.traverse_generic_file

        if not path:
            path = "."  # no file or directory specified

        # If a wildcard was provided, this is automatically resolved into
        # a tuple of filenames. Process these here.
        # regex pattern was specified and file_name is of type tuple with
        # filenames that match the pattern inside.
        if isinstance(path, tuple):
            for filename in path:
                if os.path.exists(filename) and os.path.isfile(filename):
                    if (
                        traversal_strategy(
                            filename,
                            handler,
                            element_selector,
                        )
                        != 0
                    ):
                        self.filecount = self.filecount + 1
                        success = 1
                else:
                    if (
                        self.__traverse_directory(
                            filename,
                            recursive,
                            handler,
                            traversal_strategy,
                            element_selector,
                        )
                        != 0
                    ):
                        # TODO don´t we have a test case for this?
                        self.filecount = self.filecount + 1
                        success = 1
        elif not os.path.exists(path):
            self.__logger.log(30, LOG_NO_FILE, path)
            self.unreadableFileCount += 1
            success = 1
        elif os.path.isfile(path):
            success = traversal_strategy(path, handler, element_selector)
            if success != 0:
                self.filecount = self.filecount + 1
        else:
            success = self.__traverse_directory(
                path,
                recursive,
                handler,
                traversal_strategy,
                element_selector,
            )

        return success

    def __traverse_directory(
        self,
        path,
        recursive,
        handler,
        traversal_strategy="",
        element_selector="",
    ):
        """
        Takes care of the traversal of a directory.
        Used as a helper in the overall traversal.
        """
        success = 0
        if recursive:
            for root, directories, filenames in safe_walk(
                path, topdown=True, followlinks=True
            ):
                root = os.path.normpath(root)
                # Update ignore lists with any .treqs-ignore
                # in current directory
                self.update_ignore_lists(root)
                # Filter directories
                directories[:] = [
                    d
                    for d in directories
                    if not self.filename_is_ignored(
                        os.path.join(root, d),
                        recursive,
                    )
                ]

                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    if self.filename_is_ignored(file_path, recursive):
                        self.ignoredFileCount += 1
                        self.__logger.log(10, LOG_IGNORE, file_path)
                        continue
                    if (
                        traversal_strategy(
                            file_path,
                            handler,
                            element_selector,
                        )
                        != 0
                    ):
                        self.filecount = self.filecount + 1
                        success = 1
        else:
            path = os.path.normpath(path)
            # Update ignore lists for current directory
            self.update_ignore_lists(path)

            listOfFiles = sorted(os.listdir(path))
            for filename in listOfFiles:
                file_path = os.path.join(path, filename)
                if os.path.isdir(file_path):
                    self.__logger.log(10, LOG_SKIP_DIR, file_path)
                    continue
                if self.filename_is_ignored(file_path, recursive):
                    self.__logger.log(10, LOG_IGNORE, file_path)
                    self.ignoredFileCount += 1
                    continue
                if (
                    traversal_strategy(
                        file_path,
                        handler,
                        element_selector,
                    )
                    != 0
                ):
                    self.filecount = self.filecount + 1
                    success = 1
        return success

    def import_treqs_ignore(self, treqs_ignore_file):
        """Imports filename patterns from the .treqs-ignore file"""
        patterns = []
        try:
            with open(treqs_ignore_file, "r") as ti:
                patterns = []
                for line in ti:
                    stripped = line.strip()
                    if stripped and not line.startswith("#"):
                        patterns.append(stripped)
        except FileNotFoundError:
            pass
        return patterns

    def compile_ignore_list(self, recursive):
        result = []
        for pattern in self.ignore_list:
            for f in glob.glob(pattern, recursive=recursive):
                f = os.path.normpath(f)
                result.append(f)
        return result

    def filename_is_ignored(self, file_name, recursive):
        """Check if file is in the appropriate ignore list"""
        normalized_file_name = os.path.normpath(file_name)
        if recursive:
            return normalized_file_name in self.compiled_recursive_ignore_list
        return normalized_file_name in self.compiled_non_recursive_ignore_list

    def traverse_XML_file(self, file_name, handler, element_selector=""):
        """
        Traversal strategy for XML files.
        Iterates over all elements selected using the element_selector XPath
        statement.
        Calls the handler funct with file name and the current element.
        """
        success = 0
        self.__logger.log(10, LOG_XML, file_name)
        try:
            self.__logger.log(10, LOG_PROCESS, file_name)

            # We are reading in the file as a string and add "fake" root tags
            # around, then feed into the XML parser
            # This allows us to find treqs tags even in non-XML files
            # using an XML parser.
            with open(file_name) as xml_file:
                xml_file_string = xml_file.readlines()
                id = -1
                for line in xml_file_string:
                    id = id + 1
                    if (
                        "<!--" in line
                        or "-->" in line
                        or not (
                            # fmt: skip
                            "treqs-" in line or "root" in line
                        )
                    ):
                        xml_file_string[id] = escape(line)

            # If there is an element_selector, we use this string as an XPath
            # selector to select elements
            # NOTE ElementTree does not support all of XPath.
            # Maybe we want to consider replacing this at some point
            # if we see the need for sophisticated queries.
            if element_selector != "":
                xml_file_string = f"<treqs>{''.join(xml_file_string)}</treqs>"
                root = ET.fromstring(
                    xml_file_string, parser=ET.XMLParser(recover=True)
                )

                for element in root.findall(element_selector):
                    if handler(file_name, element) != 0:
                        success = 1

            # If there is no element_selector, we assume that the relevant
            # elements are directly under the root.
            # We also assume that the document has a root tag.
            else:
                root = ET.fromstring("".join(xml_file_string))
                for element in root:
                    if handler(file_name, element) != 0:
                        success = 1

        # Currently just ignore parse errors,
        # we consider this a success for now
        except ET.ParseError as err:
            self.__logger.log(10, LOG_PARSE_ERR, file_name, str(err.args))
            self.corruptFileCount += 1
            return 0

        except UnicodeDecodeError:
            self.__logger.log(10, LOG_DEC_ERR, file_name)
            self.unreadableFileCount += 1
            return 0
        except Exception as re:
            self.__logger.log(10, LOG_GEN_ERR, file_name, str(re.args))
            self.unreadableFileCount += 1
            return 0

        return success

    # Generic traversal strategy. Just calls the handler with the file name
    # attribute. The handler function decides what to do with the file
    # NOTE Currently the element_selector is unused, but we might consider
    # just searching for it in terms of a full-text search.
    # In that case, unclear what we'd return, though.
    def traverse_generic_file(
        self,
        file_name,
        handler,
        element_selector="",
    ):
        self.__logger.log(10, LOG_PROCESS, file_name)
        return handler(file_name)


def safe_walk(path, topdown=True, followlinks=True):
    visited = set()
    for root, dirs, files in os.walk(
        path, topdown=topdown, followlinks=followlinks
    ):
        # Get the (device, inode) tuple for the current directory
        try:
            stat = os.stat(root)
        except OSError:
            continue
        dir_id = (stat.st_dev, stat.st_ino)
        if dir_id in visited:
            # Already visited this directory (cycle detected)
            dirs[:] = []  # Don't descend further
            continue
        visited.add(dir_id)
        yield root, dirs, files

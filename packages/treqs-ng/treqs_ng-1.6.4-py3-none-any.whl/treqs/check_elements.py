import io
import logging
import os
import sys
import time

import yaml

from treqs.extension_loader import load_resolver_callback
from treqs.list_elements import list_elements
from treqs.treqs_element import treqs_element

# Error messages for findings
ERR_NO_ID = "Element does not have an id."
ERR_DUP_ID = "Element id is duplicated."
ERR_NO_TYPE = "Element has an empty or missing type."
ERR_UNKNOWN_TYPE = "Element has an unrecognized type: '%s'"
ERR_UNKNOWN_OUTLINK = "Unrecognised outlink type %s within element of type %s."
ERR_UNKNOWN_INLINK = "Unrecognised inlink type %s within element of type %s."
ERR_MISSING_OUTLINKS = "Required outlinks missing: %s"
ERR_MISSING_INLINKS = "Required inlinks missing: %s"
ERR_NON_EXISTENT = "Element references non-existent element with id '%s'"
ERR_SOURCE = (
    "``%s`` linked by element '%s' needs to be linked from a ``%s``, "
    # fmt: skip
    "but linked from a ``%s`` instead."
)
ERR_SOURCES = (
    "``%s`` linked by element '%s' needs to be linked from one of these"
    "``%s``, "
    # fmt: skip
    "but linked from a ``%s`` instead."
)
ERR_TARGET = (
    "``%s`` link to element '%s' needs to point to a ``%s``, "
    # fmt: skip
    "but points to a ``%s`` instead."
)
ERR_TARGETS = (
    "``%s`` link to element '%s' needs to point to one of these ``%s``, "
    # fmt: skip
    "but points to a ``%s`` instead."
)


class check_elements:
    def __init__(self, output="table", verbose=False, testing=False):
        self.__output = output
        self.__verbose = verbose
        self.__testing = testing

        self.__logger = logging.getLogger("treqs-on-git.treqs-ng")
        self.__logger.setLevel(
            logging.DEBUG if self.__verbose else logging.INFO
        )

        # Clear previous handlers to avoid duplicates
        if not self.__testing and self.__logger.hasHandlers():
            self.__logger.handlers.clear()

        # if output == 'json' and verbose:
        if self.__output == "json" and self.__verbose:
            # Log to memory
            self.__log_stream = io.StringIO()
            handler = logging.StreamHandler(self.__log_stream)
            handler.setLevel(logging.DEBUG)
            self.__logger.addHandler(handler)
        else:
            # Log to console (for table)
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(
                logging.DEBUG if self.__verbose else logging.INFO
            )
            formatter = logging.Formatter("%(message)s")
            console_handler.setFormatter(formatter)
            self.__logger.addHandler(console_handler)
            self.__log_stream = None

        # Load resolver from extensions for external element
        # resolution
        resolver_callback = load_resolver_callback()
        self.__list_elements = list_elements(None, resolver_callback)
        self.__ttim_outlink_types = dict()
        self.__ttim_required = dict()
        self.__ttim_inlink_types = dict()
        self.__ttim_required_inlinks = dict()

        self.__element_dict = dict()
        self.__no_type_list = []
        self.__duplicate_id_dict = dict()
        self.__invalid_id_list = []

        # A dictionary with findings per element.
        self.__findings_per_uid = dict()

        self.__logger.log(10, "check_elements created")

    def fileCount(self):
        return self.__list_elements.traverser.filecount

    def findingsForUID(self, uid):
        if uid not in self.__findings_per_uid.keys():
            # Remember, we could have duplicate IDs...
            self.__findings_per_uid[uid] = []
        return self.__findings_per_uid[uid]

    def reportFindingForElement(self, message: str, element: treqs_element):
        f = finding(message, element)
        if element.uid is None or element.uid == "":
            self.findingsForUID("no valid id").append(f)
        else:
            self.findingsForUID(element.uid).append(f)
        return f

    def getFindings(self) -> dict:
        return self.__findings_per_uid

    def uidWithFinding(self):
        return self.__findings_per_uid.keys()

    def __check_treqs_element_list(self, element_list):
        success = 0
        self.__findings_per_uid.clear()

        # Actually check each individual element
        for element in element_list:
            if self.__check_treqs_element(element) != 0:
                success = 1

        # Post-hoc check: Now that the __element_id_set is complete,
        # we can check whether sources exist and their types are fitting
        for element in element_list:
            # Only process valid elements
            if element.treqs_type in self.__ttim_inlink_types:
                for link in element.inlinks:
                    # Only process link types that are recognized per TTIM
                    if (
                        link.tlt
                        in self.__ttim_inlink_types[element.treqs_type]
                    ):
                        if link.source not in self.__element_dict:
                            success = 1
                            self.reportFindingForElement(
                                "Element is referenced by non-existent "
                                f"element with id '{link.source}'",
                                element,
                            )
                        else:
                            # If the link has a target type constraint,
                            # check whether it is met
                            source_type = self.__ttim_inlink_types[
                                element.treqs_type
                            ]
                            source_link = source_type[link.tlt]
                            if source_link is not None:
                                if not is_type_contained(
                                    self.__element_dict[
                                        link.source
                                    ].treqs_type,
                                    source_link,
                                ):
                                    success = 1
                                    if not isinstance(
                                        source_link,
                                        list,
                                    ):
                                        self.reportFindingForElement(
                                            ERR_SOURCE
                                            % (
                                                link.tlt,
                                                link.source,
                                                source_link,
                                                self.__element_dict[
                                                    link.source
                                                ].treqs_type,
                                            ),
                                            element,
                                        )
                                    else:
                                        self.reportFindingForElement(
                                            ERR_SOURCES
                                            % (
                                                link.tlt,
                                                link.source,
                                                self.__ttim_inlink_types[
                                                    element.treqs_type
                                                ][link.tlt],
                                                self.__element_dict[
                                                    link.source
                                                ].treqs_type,
                                            ),
                                            element,
                                        )

        # Post-hoc check: Now that the __element_id_set is complete,
        # we can check whether targets exist and their types are fitting
        for element in element_list:
            # Only process valid elements
            if element.treqs_type in self.__ttim_outlink_types:
                for link in element.outlinks:
                    # Only process link types that are recognized per TTIM
                    if (
                        link.tlt
                        in self.__ttim_outlink_types[element.treqs_type]
                    ):
                        # Use get_element_with_uid to support external
                        # ID resolution
                        target_element = self.__get_treqs_element(link.target)
                        if target_element is None:
                            success = 1
                            self.reportFindingForElement(
                                "Element references non-existent element "
                                f"with id '{link.target}'",
                                element,
                            )
                        else:
                            # If the link has a target type constraint,
                            # check whether it is met
                            target_type = self.__ttim_outlink_types[
                                element.treqs_type
                            ]
                            target_link = target_type[link.tlt]
                            if target_link is not None:
                                if not is_type_contained(
                                    target_element.treqs_type,
                                    target_link,
                                ):
                                    success = 1
                                    if not isinstance(
                                        target_link,
                                        list,
                                    ):
                                        self.reportFindingForElement(
                                            ERR_TARGET
                                            % (
                                                link.tlt,
                                                link.target,
                                                target_link,
                                                target_element.treqs_type,
                                            ),
                                            element,
                                        )
                                    # I Do not think that this case can happen.
                                    # elif len(
                                    # self.__ttim_types[element.treqs_type]
                                    # [link.tlt]) == 1:
                                    #    self.reportFindingForElement(
                                    # element=element,
                                    # message=str(
                                    # "'%s' link to element %s needs to point
                                    # to a %s, but points to a %s instead.",
                                    # link.tlt,
                                    # link.target,
                                    # self.__ttim_types[element.treqs_type]
                                    # [link.tlt][0],
                                    # self.__element_dict[link.target]
                                    # .treqs_type))
                                    else:
                                        self.reportFindingForElement(
                                            ERR_TARGETS
                                            % (
                                                link.tlt,
                                                link.target,
                                                self.__ttim_outlink_types[
                                                    element.treqs_type
                                                ][link.tlt],
                                                target_element.treqs_type,
                                            ),
                                            element,
                                        )

        # Reporting: List all check errors
        if len(self.__duplicate_id_dict) != 0:
            for element, file_name in self.__duplicate_id_dict.items():
                self.reportFindingForElement(ERR_DUP_ID, element)

        if len(self.__invalid_id_list) != 0:
            for element in self.__invalid_id_list:
                self.reportFindingForElement(ERR_NO_ID, element)

        if len(self.__no_type_list) != 0:
            for element in self.__no_type_list:
                self.reportFindingForElement(ERR_NO_TYPE, element)

        return success

    def check_elements(self, file_name, recursive, ttim_path):
        ts = time.time()

        self.__logger.log(10, "Processing TTIM at %s", ttim_path)
        success = self.load_ttim(ttim_path)

        errorsFound = 0

        if success == 0:
            # If TTIM processed successfully, traverse the file tree
            # with the XML strategy and the XPath selector
            # to get all treqs-elements somewhere in the tree.
            element_list = self.__list_elements.get_element_list(
                file_name,
                None,
                recursive,
                inlinks=True,
            )
            success = self.__check_treqs_element_list(element_list)

            if (
                self.__output == "table"
                and len(self.__findings_per_uid.keys()) > 0
            ):
                self.__logger.log(20, "| Error location | Error | File:Line |")
                self.__logger.log(20, "| :--- | :--- | :--- |")

            if self.__output == "table":
                for uid in self.__findings_per_uid.keys():
                    for f in self.__findings_per_uid[uid]:
                        self.__logger.log(
                            30,
                            "| Element %s | %s | %s:%s |",
                            f.element.uid,
                            f.message,
                            f.element.file_name,
                            f.element.placement,
                        )
                        errorsFound += 1

        ts = time.time() - ts
        summary = ""

        if success == 0:
            summary = (
                "treqs check: checked %s files "
                "(%s files ignored, %s files unreadable, "
                "%s files corrupt) in %.2fs. OK."
                % (
                    self.fileCount(),
                    self.__list_elements.traverser.ignoredFileCount,
                    self.__list_elements.traverser.unreadableFileCount,
                    self.__list_elements.traverser.corruptFileCount,
                    ts,
                )
            )
            if self.__output == "table":
                self.__logger.log(20, summary)
        else:
            summary = (
                "treqs check: checked %s files in %.2fs. "
                "Exited with %s failed checks."
                % (self.fileCount(), ts, errorsFound)
            )
            if self.__output == "table":
                self.__logger.log(30, summary)

        if self.__output == "json":
            result = {
                "success": success == 0,
                "summary": summary,
                "findings": [
                    {
                        "uid": uid,
                        "message": finding.message,
                        "file name": finding.element.file_name,
                        "line": finding.element.placement,
                        "type": finding.element.treqs_type,
                    }
                    for uid, findings in self.__findings_per_uid.items()
                    for finding in findings
                ],
            }
            if self.__verbose:
                result["log"] = (
                    self.__log_stream.getvalue().splitlines()
                    if self.__log_stream
                    else []
                )
            return result
        else:
            if self.__testing:
                return success
            sys.exit(success)

    def __check_treqs_element(self, element):
        success = 0

        if element.treqs_type == "" or element.treqs_type is None:
            success = 1
            self.__no_type_list.append(element)

        if element.uid == "" or element.uid is None:
            success = 1
            self.__invalid_id_list.append(element)

        if element.uid in self.__element_dict:
            otherElement = self.__element_dict[element.uid]
            success = 1
            self.__duplicate_id_dict[element] = element.file_name
            if otherElement not in self.__duplicate_id_dict.keys():
                self.__duplicate_id_dict[otherElement] = otherElement.file_name
        else:
            self.__element_dict[element.uid] = element

        if element.treqs_type not in self.__ttim_outlink_types:
            self.reportFindingForElement(
                ERR_UNKNOWN_TYPE % element.treqs_type,
                element,
            )
            return 1
        else:
            # make a copy of our ttim required inlinks that we can
            # then 'tick off'
            missing_traces = self.__ttim_required_inlinks[
                element.treqs_type
            ].copy()
            for link in element.inlinks:
                source_element = self.__get_treqs_element(link.source)
                # Only process link types that are recognized per TTIM
                if (
                    (
                        link.tlt
                        not in self.__ttim_inlink_types.get(
                            element.treqs_type, []
                        )
                    )
                    # If type has no inlinks, we do not want to
                    # report an error
                    and (
                        link.tlt
                        not in self.__ttim_outlink_types.get(
                            source_element.treqs_type, []
                        )
                    )
                ):
                    self.reportFindingForElement(
                        ERR_UNKNOWN_INLINK % (link.tlt, element.treqs_type),
                        element,
                    )
                    success = 1
                else:
                    # "Cross off" required links
                    # Check whether outgoing required traces exist
                    if link.tlt in missing_traces:
                        missing_traces.remove(link.tlt)

            if len(missing_traces) > 0:
                self.reportFindingForElement(
                    ERR_MISSING_INLINKS % missing_traces,
                    element,
                )
                success = 1

            # make a copy of our ttim required links that we can
            # then 'tick off'
            missing_traces = self.__ttim_required[element.treqs_type].copy()
            for link in element.outlinks:
                target_element = self.__get_treqs_element(link.target)

                # Skip validation if target element cannot be
                # resolved (will be reported in post-hoc check)
                if target_element is None:
                    continue

                # Only process link types that are recognized per TTIM
                if (
                    link.tlt
                    not in self.__ttim_outlink_types.get(
                        element.treqs_type, []
                    )
                ) and (
                    link.tlt
                    not in self.__ttim_inlink_types.get(
                        target_element.treqs_type, []
                    )
                ):
                    self.reportFindingForElement(
                        ERR_UNKNOWN_OUTLINK % (link.tlt, element.treqs_type),
                        element,
                    )
                    success = 1
                else:
                    # "Cross off" required links
                    # Check whether outgoing required traces exist
                    if link.tlt in missing_traces:
                        missing_traces.remove(link.tlt)

            if len(missing_traces) > 0:
                self.reportFindingForElement(
                    ERR_MISSING_OUTLINKS % missing_traces,
                    element,
                )
                success = 1

        return success

    def load_ttim(self, ttim_path):
        if os.path.isfile(ttim_path):
            # Open the ttim
            with open(ttim_path) as ttim_file:
                ttim_json = yaml.safe_load(ttim_file)
                # Process TTIM
                for current_type in ttim_json["types"]:
                    # Extract all types
                    self.__ttim_outlink_types[current_type["name"]] = dict()
                    self.__ttim_inlink_types[current_type["name"]] = dict()
                    self.__ttim_required[current_type["name"]] = []
                    self.__ttim_required_inlinks[current_type["name"]] = []

                    # TODO: Add support for incoming required traces
                    # (A "type" needs to have a "relateTo" from at
                    # least one other "type")

                    # For each type, save all allowed trace types
                    # (outgoing traces)
                    outlinks_key = "outlinks"
                    if "links" in current_type.keys():
                        outlinks_key = "links"
                        self.__logger.warning(
                            "TTIM uses 'links' instead of 'outlinks'. "
                            "This is deprecated and will be removed in "
                            "the future. Please use 'outlinks' instead."
                        )
                    if outlinks_key in current_type.keys():
                        for current_link in current_type[outlinks_key]:
                            type_dict = self.__ttim_outlink_types[
                                current_type["name"]
                            ]
                            if "type" not in current_link.keys():
                                self.__logger.warning(
                                    "Type '"
                                    + str(current_type["name"])
                                    + "', Link '"
                                    + str(current_link)
                                    + "': no type specified."
                                )
                            else:
                                link_type = current_link["type"]

                                if "target" in current_link.keys():
                                    target = current_link["target"]
                                    if not isinstance(target, list):
                                        current_link_target = target
                                    else:
                                        current_link_target = (
                                            # fmt: skip
                                            target[0]
                                            if len(target) == 1
                                            else target
                                        )
                                    type_dict[link_type] = current_link_target
                                else:
                                    type_dict[link_type] = None
                                if (
                                    "required" in current_link.keys()
                                    and is_truthy(current_link["required"])
                                ):
                                    self.__ttim_required[
                                        current_type["name"]
                                    ].append(current_link["type"])

                    # For each type, save all allowed incoming trace
                    # types (incoming traces)
                    if "inlinks" in current_type.keys():
                        for current_link in current_type["inlinks"]:
                            type_dict = self.__ttim_inlink_types[
                                current_type["name"]
                            ]
                            link_type = current_link["type"]

                            if "source" in current_link.keys():
                                source = current_link["source"]
                                if not isinstance(source, list):
                                    current_link_source = source
                                else:
                                    current_link_source = (
                                        # fmt: skip
                                        source[0]
                                        if len(source) == 1
                                        else source
                                    )
                                type_dict[link_type] = current_link_source
                            else:
                                type_dict[link_type] = None
                            if "required" in current_link.keys() and is_truthy(
                                current_link["required"]
                            ):
                                self.__ttim_required_inlinks[
                                    current_type["name"]
                                ].append(current_link["type"])

                self.__logger.log(
                    10,
                    "TTIM Configuration:\nOutlinks: %s\nInlinks: %s",
                    self.__ttim_outlink_types,
                    self.__ttim_inlink_types,
                )
                return 0

        # TODO: we want to devise a strategy for graceful error
        # handling at some point
        else:
            self.__logger.log(40, "TTIM could not be loaded at %s", ttim_path)
            return 1

    # def extract_label(self, text):
    #     # It is our convention to use the first none-empty line as label
    #     ret = "None"
    #     for line in text.splitlines():
    #         if line != "" and ret == "None":
    #             ret = line
    #     return ret

    def __get_treqs_element(self, uid) -> treqs_element:
        # Get the treqs element with the given uid
        factory = self.__list_elements.treqs_element_factory
        return factory.get_element_with_uid(uid)


# This functions checks whether a treqs-type exists in a list of
# treqs-type. This has been added to allow for backwards
# compatability where link targets could be a single treqs-type.
# In order not to break links where the target is a single type AND
# allow for multi-type targets, the functions checks for the Python
# type of the treqs_type_list variable and performs the logical
# comparison corresponding to the Python type.
def is_type_contained(treqs_type, treqs_type_list):
    if isinstance(treqs_type_list, list):
        return treqs_type in treqs_type_list
    return treqs_type == treqs_type_list


def is_truthy(value):
    """
    Returns True if the value represents a boolean 'true'
    (e.g., 'yes', 'true', '1'), False otherwise.
    Useful for interpreting config or user input.
    """
    truthy_values = {"true", "yes", "on", "1"}
    falsy_values = {"false", "no", "off", "0"}

    val = str(value).strip().lower()
    return val in truthy_values


class finding:
    def __init__(self, message: str, element: treqs_element):
        self.element = element
        self.message = message

    def __str__(self):
        return (
            f"{self.element.uid}: {self.message} "
            f"({self.element.file_name}:{self.element.placement})"
        )

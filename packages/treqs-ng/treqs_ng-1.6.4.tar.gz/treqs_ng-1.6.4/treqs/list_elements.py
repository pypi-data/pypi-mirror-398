import logging
import os.path
import sys
import time
import xml.etree.cElementTree as ET
from abc import ABC, abstractmethod
from enum import Enum

from treqs.external_id_utils import is_external_id
from treqs.file_traverser import file_traverser
from treqs.treqs_element import *


class list_elements:
    class Direction(Enum):
        INWARDS = "inlinks"
        OUTWARDS = "outlinks"

    def __init__(self, list_elements_strategy=None, resolver_callback=None):
        self.__logger = logging.getLogger("treqs-on-git.treqs-ng")
        self.traverser = file_traverser()
        self.element_list = []
        self.treqs_element_factory = treqs_element_factory(resolver_callback)
        if list_elements_strategy is None:
            self.element_lister = list_elements_md_tab_strat()
        else:
            self.element_lister = list_elements_strategy
        self.__logger.log(10, "list_elements created")

    def list_elements(
        self,
        filename,
        treqs_type,
        recursive=True,
        uid=None,
        outlinks=False,
        inlinks=False,
        followlinks=False,
        attributes=None,
        output="table",
    ):
        ts = time.time()
        self.get_element_list(
            filename,
            treqs_type,
            recursive,
            uid,
            outlinks,
            inlinks,
            attributes,
            followlinks,
        )
        if output == "json":
            return [element.to_dict() for element in self.element_list]

        if len(self.element_list) != 0:
            self.element_lister.logHeader(self.__logger, self.element_list)
            for element in self.element_list:
                self.element_lister.logElement(self.__logger, element)
                if self.list_outlinks:
                    self.element_lister.logOutlinks(
                        self.__logger,
                        element,
                        self.treqs_element_factory,
                        followlinks,
                    )
                if self.list_inlinks:
                    self.element_lister.logInlinks(
                        self.__logger,
                        element,
                        self.treqs_element_factory,
                        followlinks,
                    )
            self.element_lister.logFooter(self.__logger, self.element_list)
        else:
            self.element_lister.logEmptyList(self.__logger)

        ts = time.time() - ts
        self.__logger.log(
            20,
            "treqs list: "
            + (
                "read %s files "
                + "(%s files ignored, %s files unreadable, %s files corrupt) "
                + "in %.2fs. Found %s elements."
            )
            % (
                self.traverser.filecount,
                self.traverser.ignoredFileCount,
                self.traverser.unreadableFileCount,
                self.traverser.corruptFileCount,
                ts,
                len(self.element_list),
            ),
        )
        # Let's return the exit code.
        # sys.exit(0)
        return 0

    def get_element_list(
        self,
        file_name,
        treqs_type=None,
        recursive=True,
        uid=None,
        outlinks=False,
        inlinks=False,
        attributes=None,
        followlinks=False,
    ):
        self.treqs_type = treqs_type
        self.uid = uid
        self.list_outlinks = outlinks
        self.list_inlinks = inlinks
        self.follow_links = followlinks
        self.attributes = attributes

        self.traverser.traverse_file_hierarchy(
            file_name,
            recursive,
            self.extract_treqs_element,
            self.traverser.traverse_XML_file,
            ".//treqs-element",
        )

        # Resolve external elements from outlinks
        external_ids = set()
        for element in self.treqs_element_factory._treqs_elements.values():
            for outlink in element.outlinks:
                if is_external_id(outlink.target):
                    external_ids.add(outlink.target)

        # Also try to resolve if filtering by an external UID directly
        if self.uid and is_external_id(self.uid):
            external_ids.add(self.uid)

        for ext_id in external_ids:
            ext_element = self.treqs_element_factory.get_element_with_uid(
                ext_id
            )
            if ext_element and ext_element not in self.element_list:
                # Apply same filters as regular elements
                if (
                    self.treqs_type
                    and self.treqs_type != ext_element.treqs_type
                ):
                    continue
                if self.uid and self.uid != ext_element.uid:
                    continue
                if self.attributes and not all(
                    ext_element.attributes.get(k) == v
                    for k, v in self.attributes.items()
                ):
                    continue
                self.element_list.append(ext_element)

        # Apply attribute filtering (e.g., asil=1)
        # if attributes:
        #    self.element_list = [
        #        e for e in self.element_list
        #        if
        #        all(e.attributes.get(k) == v for k, v in attributes.items())
        #    ]

        # After we have the entire element inventory, we process
        if self.list_inlinks:
            self.process_inlinks()

        # Follow links
        return self.element_list

    def extract_treqs_element(self, file_name, element):
        te = self.treqs_element_factory.get_treqs_element(element, file_name)
        # Filter by type - return if the current element is not the one we
        # filter for.
        if self.treqs_type is not None and self.treqs_type != te.treqs_type:
            return
        # Filter by ID - return if the current element
        # does not have the right ID.
        if self.uid is not None and self.uid != te.uid:
            return

        if self.attributes is not None:
            if not all(
                # fmt: skip
                te.attributes.get(k) == v
                for k, v in self.attributes.items()
            ):
                return

        # If not filtered, we append the Treqs element to our list
        # if not te in self.element_list:
        self.element_list.append(te)

    def process_inlinks(self):
        self.treqs_element_factory.process_inlinks()


class list_elements_strategy(ABC):
    def logEmptyList(self, logger):
        logger.log(20, "treqs list did not find relevant elements.")
        return

    @abstractmethod
    def logHeader(logger, elementlist):
        pass

    @abstractmethod
    def logFooter(logger, elementlist):
        pass

    @abstractmethod
    def logElement(logger, element):
        pass

    @abstractmethod
    def logInlinks(logger, element, treqselementfactory, followLinks):
        pass

    @abstractmethod
    def logOutlinks(logger, element, treqselementfactory, followLinks):
        pass


class list_elements_md_tab_strat(list_elements_strategy):
    def logHeader(self, logger, elementlist):
        logger.log(20, "| UID | Type | Label | File:Line |")
        logger.log(20, "| :--- | :--- | :--- | :--- |")
        return

    def logFooter(self, logger, elementlist):
        pass

    def logElement(self, logger, element):
        logger.log(20, "%s", element)
        return

    def logInlinks(self, logger, element, treqselementfactory, followLinks):
        for tl in element.inlinks:
            source_te = treqselementfactory.get_element_with_uid(tl.source)
            label = source_te.label
            file_line = "{file}:{line}".format(
                file=source_te.file_name,
                line=source_te.placement,
            )
            logger.log(
                20,
                "| --inlink--> (%s) | %s | Source: %s | %s |",
                tl.source,
                tl.tlt,
                label,
                file_line,
            )
        return

    def logOutlinks(self, logger, element, element_factory, followLinks):
        for tl in element.outlinks:
            target_treqs_type = element_factory.get_element_with_uid(tl.target)
            if target_treqs_type is None:
                label = (
                    "Target treqs element not found. "
                    # fmt: skip
                    "Has the containing file been included in the scope?"
                )
                file_line = "--"
            else:
                label = target_treqs_type.label
                file_line = "{file}:{line}".format(
                    file=target_treqs_type.file_name,
                    line=target_treqs_type.placement,
                )
            logger.log(
                20,
                "| --outlink--> (%s) | %s | Target: %s | %s |",
                tl.target,
                tl.tlt,
                label,
                file_line,
            )
        return


class list_elements_plantuml_strat(list_elements_strategy):
    def __init__(self):
        # This is a set, to keep track of relevant Treqs objects
        self.__interesting_elements = set()

    def logEmptyList(self, logger):
        # TODO Replace with a plantuml comment
        logger.log(20, "treqs list did not find relevant elements.")
        return

    def logHeader(self, logger, elementlist):
        logger.log(20, "@startuml")
        if len(elementlist) != 0:
            self.__interesting_elements.clear()
            for element in elementlist:
                self.__interesting_elements.add(element.uid)

    def logFooter(self, logger, elementlist):
        logger.log(20, "@enduml")

    def logElement(self, logger, element, fallback_uid="No UID"):
        # fallback_uid="No UID"
        # fallback_uid = self.__safe_plantuml_uid(None)
        if element is None:  # This element is out of scope
            logger.log(
                20,
                'map "**%s**" as %s {',
                "OUT OF SCOPE ELEMENT",
                self.safe_plantuml_uid(fallback_uid),
            )
            logger.log(20, 'uid => ""%s""', fallback_uid)
            logger.log(20, "}")

            return

        logger.log(
            20,
            'map "**%s**" as %s {',
            element.label,
            self.safe_plantuml_uid(element.uid),
        )
        logger.log(20, 'uid => ""%s""', element.uid)
        logger.log(20, "type => //%s//", element.treqs_type)
        logger.log(
            20,
            "location => %s:%s",
            element.file_name.replace("/", "/\\n"),
            element.placement,
        )
        logger.log(20, "}")

    def logInlinks(self, logger, element, element_factory, followLinks):
        links = element.inlinks
        arrows = "-->"

        for tl in links:
            link_target = tl.source
            # The following if covers the case where you select a specific
            # element via uid, which has inlinks from another file
            if link_target not in self.__interesting_elements:
                self.__interesting_elements.add(link_target)
                target_treqs_element = element_factory.get_element_with_uid(
                    link_target,
                )
                self.logElement(
                    logger,
                    target_treqs_element,
                    fallback_uid=link_target,
                )
                if followLinks:
                    if target_treqs_element is not None:
                        self.logInlinks(
                            logger,
                            target_treqs_element,
                            element_factory,
                            followLinks,
                        )

            logger.log(
                20,
                "%s %s %s : %s",
                self.safe_plantuml_uid(link_target),
                arrows,
                self.safe_plantuml_uid(element.uid),
                tl.tlt,
            )

    def logOutlinks(self, logger, element, element_factory, followLinks):
        links = element.outlinks
        arrows = "-->"

        for tl in links:
            link_target = tl.target
            if link_target not in self.__interesting_elements:
                self.__interesting_elements.add(link_target)
                target_treqs_element = element_factory.get_element_with_uid(
                    link_target,
                )
                self.logElement(
                    logger,
                    target_treqs_element,
                    fallback_uid=link_target,
                )
                if followLinks:
                    if target_treqs_element is not None:
                        self.logOutlinks(
                            logger,
                            target_treqs_element,
                            element_factory,
                            followLinks,
                        )

            logger.log(
                20,
                "%s %s %s : %s",
                self.safe_plantuml_uid(element.uid),
                arrows,
                self.safe_plantuml_uid(link_target),
                tl.tlt,
            )

    def safe_plantuml_uid(self, uid):
        if uid is None:
            return "UNKNOWN_UID"
        return uid.replace("-", "_")

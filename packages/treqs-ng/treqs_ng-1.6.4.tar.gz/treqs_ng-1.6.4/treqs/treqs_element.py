import logging
from asyncio.events import get_event_loop
from readline import get_current_history_length
from typing import Dict
from webbrowser import get
from xml.etree import ElementTree as ET

from treqs.external_id_utils import is_external_id, parse_external_id


class treqs_element:
    def __init__(self, element: ET.Element, file_name):
        self.uid: str = element.get("id")
        self.treqs_type: str = element.get("type")
        self.file_name: str = file_name
        self.placement: int = element.sourceline
        # Extract attributes directly from the element, including 'asil'
        self.attributes: Dict[str, str] = {
            key: element.attrib[key] for key in element.attrib
        }

        # For virtual elements created from external links
        self.is_external = False

        # Store text/label
        self._text = element.text
        self._label = (
            self.extract_label(element.text) if element.text else "None"
        )

        self.outlinks = []
        self.inlinks = []
        for treqslink in element.iter("treqs-link"):
            tl = treqs_link(self.uid, treqslink, file_name)
            self.outlinks.append(tl)

    @classmethod
    def create_virtual(cls, uid, resolved_data, file_name="<virtual>"):
        """
        Create a virtual treqs_element from resolver data (for external links).

        Args:
            uid: The external ID (e.g., 'gl:#96')
            resolved_data: Dict with 'text', 'label', 'type', 'attributes'
            file_name: Source file name (defaults to "<virtual>")

        Returns:
            A treqs_element instance representing the external element
        """

        # Create a mock element object with the necessary attributes
        # (can't use ET.Element because it doesn't have sourceline attribute)
        class MockElement:
            def __init__(self):
                self.attrib = {}
                self.text = ""
                self.sourceline = 0

            def get(self, key, default=None):
                return self.attrib.get(key, default)

            def iter(self, tag):
                return []  # No child links in virtual elements

        element = MockElement()
        element.attrib["id"] = uid
        element.attrib["type"] = resolved_data.get("type", "external")
        element.text = resolved_data.get("text", "")

        # Create the element instance
        instance = cls(element, file_name)

        # Override label if provided
        if "label" in resolved_data:
            instance._label = resolved_data["label"]

        # Merge additional attributes
        if "attributes" in resolved_data:
            instance.attributes.update(resolved_data["attributes"])

        # Mark as resolved (it came from a resolver)
        instance._resolved = True
        instance.is_external = True

        return instance

    @property
    def text(self):
        """Return element text"""
        return self._text

    @text.setter
    def text(self, value):
        """Allow setting text directly"""
        self._text = value

    @property
    def label(self):
        """Return element label"""
        return self._label

    @label.setter
    def label(self, value):
        """Allow setting label directly"""
        self._label = value

    def extract_label(self, text):
        # It is our convention to use the first none-empty line as label
        ret = "None"
        for line in text.splitlines():
            if line != "" and ret == "None":
                ret = line

        return ret

    def __str__(self) -> str:
        ret_str = (
            f"| {self.uid} "
            f"| {self.treqs_type} "
            f"| {self.label} "
            f"| {self.file_name}:{self.placement} |"
        )
        return ret_str

    def to_dict(self) -> dict:
        return {
            "uid": self.uid,
            "type": self.treqs_type,
            "label": self.label,
            "file": self.file_name.replace("\\", "/"),
            "line": self.placement,
            "attributes": self.attributes,
            "inlinks": [link.to_dict() for link in self.inlinks],
            "outlinks": [link.to_dict() for link in self.outlinks],
        }


class treqs_link:
    def __init__(self, source, treqslinkelement, file_name):
        self.source = source  # expect treqs_element's uid
        self.target = treqslinkelement.get("target")  # extract from text
        # extract tracelink type from text
        self.tlt = treqslinkelement.get("type")
        self.placement = treqslinkelement.sourceline
        self.file_name = file_name

    def to_dict(self) -> dict:
        return {"source": self.source, "target": self.target, "type": self.tlt}

    def __str__(self) -> str:
        ret_str = (
            f"| {self.source} "
            f"| {self.target} "
            f"| {self.tlt} "
            f"| {self.file_name}:{self.placement} |"
        )
        return ret_str


class treqs_element_factory:
    def __init__(self, resolver_callback=None) -> None:
        self._treqs_elements: Dict[str, treqs_element] = {}
        self._resolver_callback = resolver_callback
        self._virtual_elements: Dict[
            str, treqs_element
        ] = {}  # Cache for virtual elements
        self.__logger = logging.getLogger("treqs-on-git.treqs-ng")
        self.__logger.log(10, "treqs_element_factory created")

    def get_treqs_element(
        self, element: ET.Element, file_name: str
    ) -> treqs_element:
        # Let's cache treqs elements for later use.
        key = str(element.get("id")) + str(file_name) + str(element.sourceline)

        if not self._treqs_elements.get(key):
            self._treqs_elements[key] = treqs_element(element, file_name)

        return self._treqs_elements[key]

    def process_inlinks(self):
        for te in self._treqs_elements.values():
            te.inlinks.clear()

        for te in self._treqs_elements.values():
            for tl in te.outlinks:
                target_te = self.get_element_with_uid(tl.target)
                if target_te is not None:
                    target_te.inlinks.append(tl)

    def _create_virtual_element(self, external_id):
        """
        Create a virtual element by resolving an external ID.

        Args:
            external_id: External ID like 'gl:#96' or 'jira:PROJ-123'

        Returns:
            treqs_element or None: Virtual element if resolved, None otherwise
        """
        if not self._resolver_callback:
            return None

        try:
            # Call resolver with the external ID string
            resolved_data = self._resolver_callback(external_id)
            if not resolved_data:
                return None

            # Ensure UID is set in resolved data
            if "uid" not in resolved_data:
                resolved_data["uid"] = external_id
            # Create virtual element
            virtual_element = treqs_element.create_virtual(
                uid=external_id,
                resolved_data=resolved_data,
                file_name=resolved_data["url"]
                if "url" in resolved_data
                else "NA",
            )

            self.__logger.log(
                10,
                f"Created virtual element for external ID '{external_id}'",
            )

            return virtual_element
        except Exception as e:
            self.__logger.log(
                10,
                f"Failed to create virtual element for '{external_id}': {e}",
            )
            return None

    def get_element_with_uid(self, uid):
        if uid is None:
            return None

        # First, try to find in parsed elements
        for element in self._treqs_elements.values():
            if element.uid == uid:
                return element

        # If not found, check if it's already in virtual cache
        if uid in self._virtual_elements:
            return self._virtual_elements[uid]

        # If not found and looks like external ID, try to resolve it
        if is_external_id(uid) and self._resolver_callback:
            virtual_element = self._create_virtual_element(uid)
            if virtual_element:
                # Cache the virtual element
                self._virtual_elements[uid] = virtual_element
                return virtual_element

        return None

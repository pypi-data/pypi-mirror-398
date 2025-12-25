import os
import uuid
from pathlib import Path

from treqs.treqs_element import *


class create_elements:
    def create_markdown_element(type, template_folder, label):
        uid = str(uuid.uuid1().hex)
        path = Path(os.path.join(template_folder, type + ".md"))
        if path.exists():
            result = '<treqs-element id="' + uid + '" type="' + type + '">'
            result += "\n"
            result += "\n"
            result += label
            with open(path) as temp:
                lines = temp.readlines()
                result += "\n\n"
                for line in lines:
                    result += line
            result += "\n</treqs-element>"
            return result
        else:
            result = "No matching template found"
            return result

    def create_markdown_new_template(type, template_folder, template, label):
        uid = str(uuid.uuid1().hex)
        path = Path(os.path.join(template_folder, template + ".md"))
        if path.exists():
            result = '<treqs-element id="' + uid + '" type="' + type + '">'
            result += "\n"
            result += "\n"
            result += label
            with open(path) as temp:
                lines = temp.readlines()
                result += "\n\n"
                for line in lines:
                    result += line
            result += "\n</treqs-element>"
            return result
        else:
            result = "No matching template found"
            return result

    def create_link(lt, target):
        result = '<treqs-link type="' + lt + '" target="' + target + '" />'
        return result

    def generate_id(amount):
        result = ""
        try:
            if amount > 100:
                result = "Amount cannot be larger 100."
            elif amount > 0:
                for treqs_id in range(0, amount):
                    uid = str(uuid.uuid1().hex)
                    result += uid + "\n"
                    treqs_id += 1
            else:
                result = "Amount has to be a positive integer."
        except TypeError:
            result = "Amount cannot be a string."

        return result

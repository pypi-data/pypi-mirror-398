import xml.etree.ElementTree as ET


class ImageConvertResult:
    def __init__(self):
        self.results = []

    def add_result(self, result: dict):
        self.results.append(result)

    def save_as_xml(self, file_path: str):
        root = ET.Element("images")
        for result in self.results:
            elem = ET.Element("image", result)
            root.append(elem)
        ET.indent(root, space="  ")
        tree = ET.ElementTree(root)
        tree.write(file_path, encoding="utf-8", xml_declaration=True)

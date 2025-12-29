import xml.etree.ElementTree as ET
from typing import List

ET.register_namespace("jp", "http://www.jpo.go.jp")


def merge_xml(src_xml_files: List[str], dst_xml_file: str):
    """merge specified xml files into a single all.xml

    Args:
        src_xml_files (List[str]): list of source xml file paths
        dst_xml_file (str): destination xml file path
    """
    root = ET.Element("root")
    for xml_file in src_xml_files:
        tree = ET.parse(xml_file)
        root_elem = tree.getroot()
        root.append(root_elem)
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(dst_xml_file, encoding="UTF-8", xml_declaration=True)

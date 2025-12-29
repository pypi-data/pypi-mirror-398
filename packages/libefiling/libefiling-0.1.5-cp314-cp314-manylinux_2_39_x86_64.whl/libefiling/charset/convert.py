import glob
import os
import xml.etree.ElementTree as ET

from charset_normalizer import from_path

ET.register_namespace("jp", "http://www.jpo.go.jp")


def convert_xml_charset(src_xml_path: str, dst_xml_path: str):
    """convert charset of a set of xml files and replace header.

    Args:
        src_xml_path (str): path to file to be converted.
        dst_xml_path (str): path to file to be stored.
    """
    ### インターネット出願ソフト用XMLはShift_JISでエンコードされている。
    ### これをUTF-8に変換する。
    with open(src_xml_path, "r", encoding="shift_jis") as f:
        xml = ET.fromstring(f.read())
        et = ET.ElementTree(xml)
        et.write(dst_xml_path, "utf-8", True)


def convert_xml_charset_dir(src_dir: str, dst_dir: str):
    """convert charset of xml files under src_dir to dst_dir.

    Args:
        src_dir (str): path to directory containing the xml files.
        dst_dir (str): path to directory where the translated files are stored in.
    """
    if src_dir == dst_dir:
        raise ValueError("src_dir and dst_dir must be different")
    for xml in glob.glob(f"{src_dir}/*.xml"):
        dst_xml = f"{dst_dir}/{os.path.basename(xml)}"
        convert_xml_charset(xml, dst_xml)

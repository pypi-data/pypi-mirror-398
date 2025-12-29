import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytesseract
from PIL import Image


def ocr_images(src_images: list[Path], lang: str) -> OcrResult:
    """extract text from images

    Args:
        src_images (list[Path]): _description_
        lang (str): eng, jpn

    Returns:
        OcrResult: _description_
    """
    results = OcrResult()
    for img_path in src_images:
        image = Image.open(str(img_path))
        text = pytesseract.image_to_string(image, lang)
        results.add_result(Path(img_path).name, text)
    return results


def guess_language(src_xml_path: str) -> str:
    """guess language from xml root node name

    Args:
        src_xml_path (str): path to source xml file
    """
    tree = ET.parse(src_xml_path)
    root = tree.getroot()
    element = root.find(
        "foreign-language-body", namespaces={"ns": "http://www.jpo.go.jp"}
    )

    ### if found foreign-language-body element, then English
    if element is not None:
        return "eng"
    else:
        return "jpn"


class OcrResult:
    def __init__(self):
        self.results = []

    def add_result(self, image_name: str, text: str):
        self.results.append({"image_name": image_name, "text": text})

    def save_as_json(self, file_path: str):
        results = sorted(self.results, key=lambda x: x["image_name"])
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump({"ocr_text": results}, f, ensure_ascii=False, indent=4)

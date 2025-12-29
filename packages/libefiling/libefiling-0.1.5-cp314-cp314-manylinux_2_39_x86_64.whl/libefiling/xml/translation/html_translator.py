import json
from typing import Dict, Literal

from bs4 import BeautifulSoup

from .base import Translator
from .subr import translate_xml


class HTMLTranslator(Translator):
    @property
    def translated_format(self) -> Literal["html"]:
        return "html"

    def process(self, params: Dict[str, str] = {}) -> str:
        # Currently, only 'image_size_tag' is supported as a parameter.
        image_size_tag = params.get("image_size_tag", "large")
        output = translate_xml(
            src_xml=self._xml_string,
            xsl_name=self._xsl_path,
            image_size_tag=image_size_tag,
        )
        return output

    def post_process(self, translated_string: str) -> str:
        return translated_string

    def save_as(self, translated_string: str, dst_path: str):
        with open(dst_path, "w", encoding="utf-8") as f:
            f.write(translated_string)


class HtmlToJsonTranslator(HTMLTranslator):
    def __init__(
        self, xsl_path: str, xml_string: str, translated_doctype: str, json_key: str
    ):
        super().__init__(xsl_path, xml_string, translated_doctype)
        self._json_key = json_key

    """xml -> html を実行し、html タグを除いた文字をvalueとするjsonを保存する

    Args:
        HTMLTranslator (_type_): _description_
    """

    @property
    def translated_format(self) -> Literal["json"]:
        return "json"

    def post_process(self, translated_string: str) -> str:
        soup = BeautifulSoup(translated_string, "html.parser")
        text = soup.get_text()
        return text.strip()

    def save_as(self, translated_string: str, dst_path: str):
        data = {"root": {self._json_key: translated_string}}
        with open(dst_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

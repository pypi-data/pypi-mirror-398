import json
from typing import Dict, Literal

import xmltodict

from .base import Translator
from .subr import translate_xml


class JSONTranslator(Translator):
    def __init__(
        self, xsl_path: str, xml_string: str, translated_doctype: str, force_list=None
    ):
        super().__init__(xsl_path, xml_string, translated_doctype)
        self._force_list = force_list

    @property
    def translated_format(self) -> Literal["json"]:
        return "json"

    def process(self, params: Dict[str, str] = {}) -> str:
        # Currently, params are not used.
        output = translate_xml(
            src_xml=self._xml_string,
            xsl_name=self._xsl_path,
        )
        return output

    def post_process(self, translated_string: str) -> str | dict:
        args = {}
        if self._force_list:
            args["force_list"] = self._force_list
        translated = xmltodict.parse(
            translated_string,
            strip_whitespace=False,
            **args,
        )
        return translated

    def save_as(self, translated: str | dict, dst_path: str):
        if isinstance(translated, dict):
            with open(dst_path, "w", encoding="utf-8") as f:
                json.dump(translated, f, ensure_ascii=False, indent=2)
        else:
            with open(dst_path, "w", encoding="utf-8") as f:
                f.write(translated)


class JSONImageInfoTranslator(JSONTranslator):
    def post_process(self, translated_string):
        obj = super().post_process(translated_string)
        ### { "images": {"image": [ ..., ... ] } }
        ### -> { "images": [ ..., ... ] }
        images = obj["images"]["image"]
        return {"images": images}

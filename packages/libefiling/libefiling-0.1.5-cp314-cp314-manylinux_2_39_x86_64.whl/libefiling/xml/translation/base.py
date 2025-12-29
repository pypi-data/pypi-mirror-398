from abc import ABC, abstractmethod
from typing import Dict, Literal


class Translator(ABC):
    def __init__(self, xsl_path: str, xml_string: str, translated_doctype: str):
        self._translated_doctype = translated_doctype
        self._xsl_path = xsl_path
        self._xml_string = xml_string

    @property
    def translated_doctype(self) -> str:
        return self._translated_doctype

    @property
    @abstractmethod
    def translated_format(self) -> Literal["html", "json"]:
        pass

    @abstractmethod
    def process(self, params: Dict[str, str] = {}) -> str:
        pass

    @abstractmethod
    def post_process(self, translated_string: str) -> str:
        pass

    @abstractmethod
    def save_as(self, translated_string: str, dst_path: str):
        pass

    def translate(self, dst_file_path: str, params: Dict[str, str] = {}) -> str:
        output = self.process(params)
        output = self.post_process(output)
        self.save_as(output, dst_file_path)

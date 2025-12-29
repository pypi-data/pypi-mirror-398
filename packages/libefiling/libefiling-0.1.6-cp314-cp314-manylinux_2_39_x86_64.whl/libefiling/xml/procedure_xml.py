from pathlib import Path
from tempfile import NamedTemporaryFile

from ..charset import convert_xml_charset
from .translation.resolver import xsl_resolver
from .translation.subr import translate_xml


def convert_procedure_xml(source_xml: str, dst_xml_path: str):
    with NamedTemporaryFile(delete=True, suffix=".xml") as temp_output:
        convert_xml_charset(source_xml, temp_output.name)
        xsl_path = xsl_resolver("xml/procedure.xsl")
        output = translate_xml(Path(temp_output.name), xsl_path)
        with open(dst_xml_path, "w", encoding="utf-8") as f:
            f.write(output)

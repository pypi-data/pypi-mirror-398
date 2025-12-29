from pathlib import Path
from typing import Union

import saxonche

from .resolver import xsl_resolver


def translate_xml(
    src_xml: Union[str, Path], xsl_name: str, image_size_tag: str = "large"
) -> str:
    """translate xml by xsl using saxon

    Args:
        src_xml (Union[str, Path]): path to xml file or xml string
        xsl_name (str): name of xsl file
    """
    xsl_path = xsl_resolver(xsl_name)
    # Initialize the Saxon/C processor
    with saxonche.PySaxonProcessor(license=False) as proc:
        # Create an XSLT processor
        xslt_processor = proc.new_xslt30_processor()

        # Load the XML and XSLT files
        if isinstance(src_xml, Path):
            xml_file = proc.parse_xml(xml_file_name=str(src_xml))
        else:
            xml_file = proc.parse_xml(xml_text=src_xml)

        executable = xslt_processor.compile_stylesheet(stylesheet_file=str(xsl_path))

        # パラメータを必要とするXSLは僅かだけど、全部に適用しちゃう
        # いずれ、params 辞書を受け取るようにして汎用化するかも
        executable.set_parameter(
            "image_size_tag", proc.make_string_value(image_size_tag)
        )

        # transformation
        output = executable.transform_to_string(xdm_node=xml_file)
    return output

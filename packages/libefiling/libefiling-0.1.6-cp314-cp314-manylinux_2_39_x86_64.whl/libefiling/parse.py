import glob
from pathlib import Path
from tempfile import TemporaryDirectory

from .archive.extract import extract
from .charset.convert import convert_xml_charset_dir
from .image.convert import convert_images
from .image.params import ImageConvertParam
from .metadata.get_metadata import get_metadata
from .ocr.ocr import guess_language, ocr_images
from .xml.merge import merge_xml
from .xml.procedure_xml import convert_procedure_xml
from .xml.translation.factory import get_translators

defaultImageParams: list[ImageConvertParam] = [
    {
        "width": 300,
        "height": 300,
        "suffix": "-thumbnail",
        "format": ".webp",
        "attributes": [{"key": "size_tag", "value": "thumbnail"}],
    },
    {
        "width": 600,
        "height": 600,
        "suffix": "-middle",
        "format": ".webp",
        "attributes": [{"key": "size_tag", "value": "middle"}],
    },
    {
        "width": 800,
        "height": 0,
        "suffix": "-large",
        "format": ".webp",
        "attributes": [{"key": "size_tag", "value": "large"}],
    },
]


def parse_archive(
    src_archive_path: str,
    src_procedure_path: str,
    output_dir: str,
    image_params: list[ImageConvertParam] = defaultImageParams,
):
    """parse e-filing archive and generate various outputs."""

    if not Path(src_archive_path).exists():
        raise FileNotFoundError(f"Source archive not found: {src_archive_path}")
    if not Path(src_procedure_path).exists():
        raise FileNotFoundError(f"Source procedure XML not found: {src_procedure_path}")
    if not Path(output_dir).exists():
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    with TemporaryDirectory() as temp_dir, TemporaryDirectory() as temp_xml_dir:
        ### extract archive to temp_dir
        extract(src_archive_path, temp_dir)

        ### convert charset of all xml files in temp_dir to UTF-8 and save to temp_xml_dir
        convert_xml_charset_dir(temp_dir, temp_xml_dir)

        ### convert charset of procedure xml to UTF-8 and save to temp_xml_dir
        convert_procedure_xml(src_procedure_path, f"{temp_xml_dir}/procedure.xml")

        ### convert images
        src_images = glob.glob(f"{temp_dir}/*.tif") + glob.glob(f"{temp_dir}/*.jpg")
        result = convert_images(src_images, output_dir, image_params)

        ### save conversion results as XML
        result.save_as_xml(f"{temp_xml_dir}/conversion_results.xml")

        ### merge all xml files in temp_xml_dir into a single xml file
        src_xmls = glob.glob(f"{temp_xml_dir}/*.xml") + glob.glob(
            f"{temp_xml_dir}/*.XML"
        )
        dst_xml = f"{output_dir}/document.xml"
        merge_xml(src_xmls, dst_xml)

        ### perform OCR on images and save results as JSON
        src_images = glob.glob(f"{temp_dir}/*.tif") + glob.glob(f"{temp_dir}/*.jpg")
        lang = guess_language(f"{output_dir}/document.xml")
        ocr_result = ocr_images(src_images, lang=lang)
        ocr_result.save_as_json(f"{output_dir}/ocr_results.json")

        ### generate and save metadata as JSON
        metadata = get_metadata(src_archive_path)
        metadata.save_as_json(f"{output_dir}/metadata.json")

        ### translate XML to various formats and save them
        translators = get_translators(f"{output_dir}/document.xml")
        for translator in translators:
            dst_file_path = (
                Path(output_dir)
                / f"{translator.translated_doctype}.{translator.translated_format}"
            )
            translator.translate(dst_file_path, params={"image_size_tag": "tall"})

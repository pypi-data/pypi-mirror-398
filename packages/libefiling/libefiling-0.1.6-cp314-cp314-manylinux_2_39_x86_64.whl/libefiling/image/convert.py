from pathlib import Path
from typing import Dict, List

from PIL import Image, ImageChops, ImageOps

from .kind import detect_image_kind
from .params import ImageConvertParam
from .results import ImageConvertResult


def convert_images(
    src_images: List[str], dst_dir: str, params: List[ImageConvertParam]
) -> ImageConvertResult:
    """convert images in src_images list and save them to dst_dir.

    Args:
        src_images (List[str]): list of source image paths
        dst_dir (str): destination directory path
        params (List[ImageConvertParam]): configurations for image conversion"""
    results = ImageConvertResult()
    dst_dir_path = Path(dst_dir)
    dst_dir_path.mkdir(parents=True, exist_ok=True)

    for param in params:
        attributes = (
            get_attributes(param["attributes"]) if "attributes" in param else {}
        )
        for src_image in src_images:

            ### 保存先ファイル名の生成
            suffix = param["suffix"] if param["suffix"] is not None else ""
            format = param["format"] if param["format"] is not None else ".webp"
            dst_image_path = dst_dir_path / (Path(src_image).stem + suffix + format)

            ### 画像変換の実行
            src_image_path = Path(src_image)
            converted_image = convert(src_image_path, param["width"], param["height"])
            converted_image.save(dst_image_path)

            ### 変換結果の記録
            results.add_result(
                {
                    "orig": src_image_path.name,
                    "new": dst_image_path.name,
                    "width": str(converted_image.width),
                    "height": str(converted_image.height),
                    "kind": detect_image_kind(src_image),
                    **attributes,
                }
            )

    return results


def get_attributes(attributes_param: List[Dict[str, str]]) -> Dict[str, str]:
    attributes = {}

    for attr in attributes_param:
        key = attr.get("key")
        value = attr.get("value")
        if key is not None and value is not None:
            attributes[key] = value
    return attributes


def convert(src: Path, width: int, height: int) -> Image.Image:
    image = Image.open(str(src))

    # convert a monochrome image to grayscale.
    if image.mode == "1":
        image = image.convert("L")

    # remove margins
    image = crop(image)

    # resize
    resize_size = get_size(image, width, height)
    resized_image = image.resize(resize_size, resample=Image.Resampling.LANCZOS)

    # expand image to fit given width and height.
    dw = width - resized_image.width if width > 0 else 0
    dh = height - resized_image.height if height > 0 else 0
    if dw > 0 or dh > 0:
        padding = (dw // 2, dh // 2, dw - (dw // 2), dh - (dh // 2))
        new_image = ImageOps.expand(resized_image, padding, 255)
        return new_image
    else:
        return resized_image


def crop(image: Image.Image):
    # background image
    bg = Image.new(image.mode, image.size, 255)  # image.getpixel((0, 0)))

    # difference original image and background image.
    diff = ImageChops.difference(image, bg)
    # diff = diff.filter(ImageFilter.MedianFilter(5))  too slow
    # diff = diff.point(lambda p: 255 if p > 160 else 0)

    # detect boundary to background color
    croprange = diff.getbbox()
    crop_image = image.crop(croprange)

    return crop_image


def get_size(image: Image.Image, width: int, height: int):
    x_ratio = width / image.width
    y_ratio = height / image.height

    if width == 0:
        resize_size = (round(image.width * y_ratio), height)
    elif height == 0:
        resize_size = (width, round(image.height * x_ratio))
    elif x_ratio < y_ratio:
        resize_size = (width, round(image.height * x_ratio))
    else:
        resize_size = (round(image.width * y_ratio), height)

    return resize_size

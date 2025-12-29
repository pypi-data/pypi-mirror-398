from dataclasses import dataclass
from typing import List


@dataclass
class ImageConvertParam:
    suffix: str | None
    format: str | None
    width: int
    height: int
    attributes: List[ImageAttribute]


@dataclass
class ImageAttribute:
    key: str
    value: str

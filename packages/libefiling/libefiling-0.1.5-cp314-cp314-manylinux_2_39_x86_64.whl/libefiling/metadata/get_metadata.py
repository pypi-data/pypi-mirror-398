import json

from ..utils.archive import (
    detect_document_code,
    detect_document_extension,
    detect_document_id,
    detect_document_kind,
)


def get_metadata(archive_path: str) -> Metadata:
    """generate meta data based on archive.

    meta data contains
      Document ID
      Document code, such as A163, A101;
      Archive extension, such as JWX, JPC;
      Archive kind, such as AAA, AER, NNF;

    Args:
        archive_info (ArchiveInfo): _description_
        dst_dir (Path): _description_
    """
    m = Metadata()
    m.add_metadata("id", detect_document_id(archive_path))
    m.add_metadata("code", detect_document_code(archive_path))
    m.add_metadata("ext", detect_document_extension(archive_path))
    m.add_metadata("kind", detect_document_kind(archive_path))
    return m


class Metadata:
    def __init__(self):
        self.results = {}

    def add_metadata(self, key: str, value: str):
        self.results[key] = value

    def save_as_json(self, file_path: str):
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, ensure_ascii=False, indent=4)

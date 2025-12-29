### Internet naminで送受信したファイル名に基づいて、各種データを取得する関数群
### https://www.pcinfo.jpo.go.jp/site/3_support/2_faq/pdf/09_09_file-name.pdf

from pathlib import Path


def detect_document_id(archive_path: str) -> str:
    """return document ID based on archive_path name

    Args:
        archive_path (str): archive path

    Returns:
        str: document ID
    """
    return Path(archive_path).stem


def detect_document_code(archive_path: str) -> str:
    """return document classification code based on archive_path name

    Args:
        archive_path (str): archive path

    Returns:
        str: archive code
    """
    return Path(archive_path).stem[19 : 19 + 9].replace("_", "")


def detect_document_extension(archive_path: str) -> str:
    """return document extension based on archive_path name

    Args:
        archive_path (str): archive path

    Returns:
        str: document extension
    """
    return Path(archive_path).suffix.upper()


def detect_document_kind(archive_path: str) -> str:
    """return document kind based on archive_path name

    Args:
        archive_path (str): archive path

    Returns:
        str: document kind
    """
    b = Path(archive_path).stem
    l = len(b)
    kind = b[l - 3 :].upper()
    return kind

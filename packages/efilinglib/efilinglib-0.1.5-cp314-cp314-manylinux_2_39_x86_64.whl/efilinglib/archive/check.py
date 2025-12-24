import re
from pathlib import Path
from typing import List

from pydantic import BaseModel


class ArchiveNameCheckModel(BaseModel):
    start: int
    length: int
    pattern: str


rules: List[ArchiveNameCheckModel] = [
    ArchiveNameCheckModel(start=0, length=19, pattern=r"[0-9]+_+"),
    ArchiveNameCheckModel(start=19, length=9, pattern=r"[A-Z0-9]*_+"),
    ArchiveNameCheckModel(start=28, length=12, pattern=r"[A-Z0-9]*_+"),
    ArchiveNameCheckModel(start=40, length=1, pattern=r"[0-9]"),
    ArchiveNameCheckModel(start=41, length=15, pattern=r"[A-Z0-9]*_+"),
    ArchiveNameCheckModel(start=56, length=1, pattern=r"[ANDIOPS]"),
    ArchiveNameCheckModel(
        start=57,
        length=2,
        pattern=r"AS|AA|TR|CR|RE|NF|NL|BA|AH|LG|DR|FM|HM|IM|ED",
    ),
    ArchiveNameCheckModel(start=59, length=1, pattern=r"\."),
    ArchiveNameCheckModel(
        start=60,
        length=3,
        pattern=r"JPA|JPB|JPC|JPD|JPH|JWX|JWS|XML|TXT|HTM|JPG|ZIP|DAT",
    ),
]


def check_archive_name(archive_path: Path) -> bool:
    """check archive name follows the naming rule
    in https://www.pcinfo.jpo.go.jp/site/3_support/2_faq/pdf/09_09_file-name.pdf

    Args:
        archive_name (str): the name of the archive

    Returns:
        bool: True if the archive name follows the naming rule, False otherwise
    """
    for rule in rules:
        start = rule.start
        length = rule.length
        pattern = re.compile(rf"^{rule.pattern}$")
        segment = archive_path.name[start : start + length]
        if len(segment) < length:
            return False
        match = pattern.match(segment)
        if not match:
            return False
    else:
        return True

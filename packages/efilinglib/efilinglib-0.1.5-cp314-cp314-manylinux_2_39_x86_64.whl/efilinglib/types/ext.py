from enum import Enum
from pathlib import Path


class ArchiveExt(Enum):
    """Archive extension

    see item 8th of naming rule in https://www.pcinfo.jpo.go.jp/site/3_support/2_faq/pdf/09_09_file-name.pdf
    """

    JWX = ".JWX"
    JWS = ".JWS"
    JPC = ".JPC"
    JPD = ".JPD"

    @classmethod
    def from_path(cls, archive_path: Path):
        ext = archive_path.suffix.upper()
        return ArchiveExt(ext)

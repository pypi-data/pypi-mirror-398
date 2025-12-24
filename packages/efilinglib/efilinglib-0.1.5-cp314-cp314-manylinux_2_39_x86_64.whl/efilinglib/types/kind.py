from enum import Enum
from pathlib import Path


class ArchiveKind(Enum):
    """Archive kind

    see item 6th, 7th of naming rule in https://www.pcinfo.jpo.go.jp/site/3_support/2_faq/pdf/09_09_file-name.pdf
    """

    AAA = "AAA"
    NNF = "NNF"
    AER = "AER"

    @classmethod
    def from_path(cls, archive_path: Path):
        """return kind of the Archive

        kind is last 3 characters of archive_name without extension
        """
        b = archive_path.stem
        l = len(b)
        kind = b[l - 3 :].upper()
        return ArchiveKind(kind)

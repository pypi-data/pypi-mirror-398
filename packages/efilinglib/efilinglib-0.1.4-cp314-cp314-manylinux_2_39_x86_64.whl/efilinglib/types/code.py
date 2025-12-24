from enum import Enum
from pathlib import Path


class ArchiveCode(Enum):
    """Archive code

    see item 2nd of naming rule in https://www.pcinfo.jpo.go.jp/site/3_support/2_faq/pdf/09_09_file-name.pdf
    """

    A101 = "A101"  # 特許査定
    A102 = "A102"  # 拒絶査定
    A1131 = "A1131"  # 拒絶理由通知書
    A1523 = "A1523"  # 手続補正書
    A153 = "A153"  # 意見書
    A163 = "A163"  # 特許願
    A1631 = "A1631"  # 翻訳文提出書
    A1632 = "A1632"  # 国内書面
    A1634 = "A1634"  # 国際出願翻訳文提出書

    @classmethod
    def from_path(cls, archive_path: Path):
        """return code of the Archive

        According to the file naming rules, from the 20th character counting from 1st, 9 characters are used.

        Args:
            archive_path (Path): archive path

        Returns:
            ArchiveCode: archive code
        """
        code = archive_path.stem[19 : 19 + 9].replace("_", "")
        return ArchiveCode(code)

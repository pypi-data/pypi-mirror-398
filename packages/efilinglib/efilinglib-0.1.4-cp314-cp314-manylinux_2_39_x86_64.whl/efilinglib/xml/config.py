from typing import NamedTuple
from ..xml.kind import FileKind


class XmlConversionConfig(NamedTuple):
    src_kind: FileKind
    xsl_name: str
    dst_filename: FileKind

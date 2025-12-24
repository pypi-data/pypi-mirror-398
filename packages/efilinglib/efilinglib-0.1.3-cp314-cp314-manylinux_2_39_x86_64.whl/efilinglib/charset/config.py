from re import Pattern
from typing import NamedTuple


class CharsetConversionConfig(NamedTuple):
    patterns: Pattern
    src_encoding: str
    dst_encoding: str = 'UTF-8'

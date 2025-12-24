from typing import NamedTuple, Literal
from .kind import ImageKind


class ImageConversionConfig(NamedTuple):
    apply_to: ImageKind | Literal['all']
    size_tag: str
    width: int
    height: int
    suffix: str
    format: str

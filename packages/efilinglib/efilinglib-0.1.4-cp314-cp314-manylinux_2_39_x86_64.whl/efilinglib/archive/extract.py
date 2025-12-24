from pathlib import Path
from typing import List, Tuple

from ..types.ext import ArchiveExt
from ..types.kind import ArchiveKind
from .aaa import (
    ArchiveHandlerAAAJPC,
    ArchiveHandlerAAAJPD,
    ArchiveHandlerAAAJWS,
    ArchiveHandlerAAAJWX,
)
from .check import check_archive_name
from .handler import ArchiveHandler
from .nnf import ArchiveHandlerNNFJPC, ArchiveHandlerNNFJWS, ArchiveHandlerNNFJWX


def extract_archive(archive_path: Path) -> List[Tuple[str, bytes]]:
    """extract all files from the archive.

    Args:
        archive_path (Path): Path of the archive
        content (bytes): content of the archive file
    """
    if check_archive_name(archive_path) is False:
        raise ValueError(f"archive name {archive_path.name} is invalid")

    handler = create_handler(archive_path)
    return handler.get_contents()


def create_handler(archive_path: Path) -> "ArchiveHandler":
    """factory method to create an instance of ArchiveHandler

    Args:
        archive_path (Path): Path of the archive

    Returns:
        ArchiveHandler: an instance of ArchiveHandler
    """
    ext = ArchiveExt.from_path(archive_path)
    kind = ArchiveKind.from_path(archive_path)

    if kind == ArchiveKind.AAA or kind == ArchiveKind.AER:
        if ext == ArchiveExt.JWX:
            handler = ArchiveHandlerAAAJWX
        elif ext == ArchiveExt.JWS:
            handler = ArchiveHandlerAAAJWS
        elif ext == ArchiveExt.JPC:
            handler = ArchiveHandlerAAAJPC
        elif ext == ArchiveExt.JPD:
            handler = ArchiveHandlerAAAJPD
        else:
            raise ValueError(f"unknwon file format: {archive_path}")
        # extension 'JPB' is not supported due to the lack of actual data
        # if ext == ArchiveExt.JPB:
        #     return unkown
    elif kind == ArchiveKind.NNF:
        if ext == ArchiveExt.JWX:
            handler = ArchiveHandlerNNFJWX
        elif ext == ArchiveExt.JWS:
            handler = ArchiveHandlerNNFJWS
        elif ext == ArchiveExt.JPC:
            handler = ArchiveHandlerNNFJPC
        else:
            raise ValueError(f"unknwon file format: {archive_path}")
        # extension JPD and JPB is not supported due to the lack of actual data
        # elif self.kind == ArchiveKind.NNF:
        #     if ext == ArchiveExt.JPD:
        #         return unknown
        #     if ext == ArchiveExt.JPB:
        #         return unknown
    else:
        raise ValueError(f"unknwon file format: {archive_path}")

    with archive_path.open("rb") as stream:
        archive_handler = handler(stream.read())
    return archive_handler

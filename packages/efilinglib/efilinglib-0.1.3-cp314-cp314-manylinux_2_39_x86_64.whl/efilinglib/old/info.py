from pathlib import Path

from ..types.code import ArchiveCode
from ..types.ext import ArchiveExt
from ..types.kind import ArchiveKind


class InvalidArchive(Exception):
    pass


class ArchiveInfo(object):
    """this class handles a pair of the archive and the procedure files

    the archive: *.JWX, *.JWS, *.JPD, *.JPC
    the procedure: *.XML
    """

    def __init__(self, archive: Path):
        # the archive used in Internet Application Software has an unique name.
        # use the archive name without suffix as ID
        try:
            self.id = archive.stem
            self.archive = archive
            self.kind = ArchiveKind.from_path(archive)
            self.code = ArchiveCode.get_code(archive)
            self.ext = ArchiveExt.get_ext(archive)
        except ValueError as e:
            raise InvalidArchive

        self.procedure = self.__get_procedure(archive)

    def __get_procedure(self, archive: Path) -> Path:
        # self.basename = AAAAAAAAAAAAAAAA___AAA.JWX
        # ->
        # b = AAAAAAAAAAAAAAAA___
        b = archive.name[0:-7]
        p = None
        if self.kind == ArchiveKind.AAA or self.kind == ArchiveKind.AER:
            p = Path(archive.parent) / (b + "AFM.XML")
        elif self.kind == ArchiveKind.NNF:
            p = Path(archive.parent) / (b + "NFM.XML")

        import glob

        print(glob.glob("/data/*"))
        if p and p.exists():
            return p
        else:
            raise FileNotFoundError(
                'No procedure file found corresponding to "{}"'.format(archive)
            )

    def get_archive_handler(self) -> ArchiveHandler:
        if self.kind == ArchiveKind.AAA or self.kind == ArchiveKind.AER:
            if self.ext == ArchiveExt.JWX:
                handler = ArchiveHandlerAAAJWX
            elif self.ext == ArchiveExt.JWS:
                handler = ArchiveHandlerAAAJWS
            elif self.ext == ArchiveExt.JPC:
                handler = ArchiveHandlerAAAJPC
            elif self.ext == ArchiveExt.JPD:
                handler = ArchiveHandlerAAAJPD
            else:
                raise ValueError("unknwon file format: " + self.archive)
            # extension 'JPB' is not supported due to the lack of actual data
            # if self.ext == ArchiveExt.JPB:
            #     return unkown
        elif self.kind == ArchiveKind.NNF:
            if self.ext == ArchiveExt.JWX:
                handler = ArchiveHandlerNNFJWX
            elif self.ext == ArchiveExt.JWS:
                handler = ArchiveHandlerNNFJWS
            elif self.ext == ArchiveExt.JPC:
                handler = ArchiveHandlerNNFJPC
            else:
                raise ValueError("unknwon file format: " + self.archive)
            # extension JPD and JPB is not supported due to the lack of actual data
            # elif self.kind == ArchiveKind.NNF:
            #     if self.ext == ArchiveExt.JPD:
            #         return unknown
            #     if self.ext == ArchiveExt.JPB:
            #         return unknown
        else:
            raise ValueError("unknwon file format: " + self.archive)

        with open(self.archive, "rb") as stream:
            archive_handler = handler(stream.read())
        return archive_handler

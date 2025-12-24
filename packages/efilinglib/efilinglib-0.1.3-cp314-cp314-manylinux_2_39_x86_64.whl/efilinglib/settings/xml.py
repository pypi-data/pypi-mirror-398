import re
from typing import List, Dict, Union
from ..xml.filetypes import XSLType
from ..xml.config import XmlConversionConfig as XCC
from ..xml.kind import FileKind
from ..types.code import ArchiveCode

xml_file_patterns: Dict[FileKind, Union[str, re.Pattern]] = {
    FileKind.PROCEDURE: re.compile('.+[an]fm.xml', re.IGNORECASE),
    FileKind.APPB: 'JPOXMLDOC01-appb.xml',
    FileKind.JPBIBL: 'JPOXMLDOC01-jpbibl.xml',
    FileKind.JPFLST: re.compile('.+-jpflst.xml', re.IGNORECASE),
    FileKind.PKDA: 'JPOXMLDOC01-pkda.xml',
    FileKind.PKGH: 'JPOXMLDOC01-pkgh.xml',
    FileKind.JPFOLB: 'JPOXMLDOC01-jpfolb.xml',
    FileKind.JPMNGT: re.compile('.+-jpmngt.xml', re.IGNORECASE),
    FileKind.JPNTCE: re.compile('.+-jpntce.xml', re.IGNORECASE),
    FileKind.MERGED: 'merge.xml',
    FileKind.PROCEDURE_PARAMS: 'procedure-params.xml',
    FileKind.IMAGE_MAP: 'image-map.xml',
    FileKind.METADATA: 'metadata.xml',
    FileKind.ALL: 'all.xml',
    FileKind.FILED_DOCUMENTS: 'filed_documents.html',
    FileKind.APPLICATION: 'application.html',
    FileKind.ABSTRACT: 'abstract.html',
    FileKind.CLAIMS: 'claims.html',
    FileKind.DESCRIPTION: 'description.html',
    FileKind.DRAWINGS: 'drawings.html',
    FileKind.DOCUMENT_INFO: 'data1.xml',
    FileKind.IMAGE_INFO: 'data2.xml',
    FileKind.DISPATCHED_DOC: 'dispatched.html',
    FileKind.PROSECUTION_DOC: 'prosecution.html',
    FileKind.PROSECUTION_FRAG_DOC: 'prosecution-frag.html',
    FileKind.OCR_TEXT: 'ocr-text.xml',
}


common_procedure_config = XCC(
    FileKind.PROCEDURE, 'xml/procedure.xsl', FileKind.PROCEDURE_PARAMS)

xsl_config_set: Dict[str, Dict[XSLType, List[XCC]]] = {
    'application-body': {
        XSLType.PROCEDURE: [common_procedure_config],
        XSLType.HTML: [
            XCC(FileKind.MERGED, 'xml/merge.xsl', FileKind.ALL),
            XCC(FileKind.ALL, 'html/pat-appd.xsl',
                FileKind.FILED_DOCUMENTS),
            XCC(FileKind.ALL, 'html/application.xsl', FileKind.APPLICATION),
            XCC(FileKind.ALL, 'html/abstract.xsl', FileKind.ABSTRACT),
            XCC(FileKind.ALL, 'html/claims.xsl', FileKind.CLAIMS),
            XCC(FileKind.ALL, 'html/description.xsl', FileKind.DESCRIPTION),
            XCC(FileKind.ALL, 'html/drawings.xsl', FileKind.DRAWINGS),
        ],
        XSLType.XML: [
            XCC(FileKind.ALL, 'xml/pat-appd.xsl', FileKind.DOCUMENT_INFO),
            XCC(FileKind.ALL, 'xml/images.xsl', FileKind.IMAGE_INFO),
        ],
    },
    r'{http://www.jpo.go.jp}foreign-language-body': {
        XSLType.PROCEDURE: [common_procedure_config],
        XSLType.HTML: [
            XCC(FileKind.MERGED, 'xml/merge.xsl', FileKind.ALL),
            XCC(FileKind.ALL, 'html/foreign-language-body.xsl',
                FileKind.FILED_DOCUMENTS),
            XCC(FileKind.ALL, 'html/foreign-language-body.application.xsl',
                FileKind.APPLICATION),
            XCC(FileKind.ALL, 'html/foreign-language-body.abstract.xsl',
                FileKind.ABSTRACT),
            XCC(FileKind.ALL, 'html/foreign-language-body.claims.xsl', FileKind.CLAIMS),
            XCC(FileKind.ALL, 'html/foreign-language-body.description.xsl',
                FileKind.DESCRIPTION),
            XCC(FileKind.ALL, 'html/foreign-language-body.drawings.xsl',
                FileKind.DRAWINGS),
        ],
        XSLType.XML: [
            XCC(FileKind.ALL, 'xml/foreign-language-body.xsl',
                FileKind.DOCUMENT_INFO),
            XCC(FileKind.ALL, 'xml/images.xsl', FileKind.IMAGE_INFO),
        ],
    },
    r'{http://www.jpo.go.jp}pat-app-doc': {
        XSLType.PROCEDURE: [common_procedure_config],
        XSLType.HTML: [
            XCC(FileKind.MERGED, 'xml/merge.xsl', FileKind.ALL),
            XCC(FileKind.ALL, 'html/pat-appd.xsl',
                FileKind.FILED_DOCUMENTS),
        ],
        XSLType.XML: [
            XCC(FileKind.ALL, 'xml/pat-appd.xsl', FileKind.DOCUMENT_INFO),
        ],
    },
    r'{http://www.jpo.go.jp}pat-rspns': {
        XSLType.PROCEDURE: [common_procedure_config],
        XSLType.HTML: [
            XCC(FileKind.MERGED, 'xml/merge.xsl', FileKind.ALL),
            XCC(FileKind.ALL, 'html/pat-rspn.xsl',
                FileKind.PROSECUTION_DOC),
            XCC(FileKind.ALL, 'html/pat-rspn.frag.xsl',
                FileKind.PROSECUTION_FRAG_DOC),
        ],
        XSLType.XML: [
            XCC(FileKind.ALL, 'xml/pat-rspn.xsl', FileKind.DOCUMENT_INFO),
        ],
    },
    r'{http://www.jpo.go.jp}pat-amnd': {
        XSLType.PROCEDURE: [common_procedure_config],
        XSLType.HTML: [
            XCC(FileKind.MERGED, 'xml/merge.xsl', FileKind.ALL),
            XCC(FileKind.ALL, 'html/pat-amnd.xsl',
                FileKind.PROSECUTION_DOC),
            XCC(FileKind.ALL, 'html/pat-amnd.frag.xsl',
                FileKind.PROSECUTION_FRAG_DOC),
        ],
        XSLType.XML: [
            XCC(FileKind.ALL, 'xml/pat-amnd.xsl', FileKind.DOCUMENT_INFO),
        ],
    },
    r'{http://www.jpo.go.jp}cpy-notice-pat-exam': {
        XSLType.PROCEDURE: [common_procedure_config],
        XSLType.HTML: [
            XCC(FileKind.MERGED, 'xml/merge.xsl', FileKind.ALL),
            XCC(FileKind.ALL, 'html/cpy-ntc-pat-e.xsl',
                FileKind.PROSECUTION_DOC),
            XCC(FileKind.ALL, 'html/cpy-ntc-pat-e.frag.xsl',
                FileKind.PROSECUTION_FRAG_DOC),
        ],
        XSLType.XML: [
            XCC(FileKind.ALL, 'xml/cpy-ntc-pat-e.xsl',
                FileKind.DOCUMENT_INFO),
        ],
    },
    r'{http://www.jpo.go.jp}cpy-notice-pat-exam-rn': {
        XSLType.PROCEDURE: [common_procedure_config],
        XSLType.HTML: [
            XCC(FileKind.MERGED, 'xml/merge.xsl', FileKind.ALL),
            XCC(FileKind.ALL, 'html/cpy-ntc-pat-e-rn.xsl',
                FileKind.PROSECUTION_DOC),
            XCC(FileKind.ALL, 'html/cpy-ntc-pat-e-rn.frag.xsl',
                FileKind.PROSECUTION_FRAG_DOC),
        ],
        XSLType.XML: [
            XCC(FileKind.ALL, 'xml/cpy-ntc-pat-e.xsl',  # same  {http://www.jpo.go.jp}cpy-notice-pat-exam
                FileKind.DOCUMENT_INFO),
        ],
    },
}

code_to_main_file_kind: Dict[ArchiveCode, FileKind] = {
    ArchiveCode.A163: [FileKind.APPB, FileKind.JPFOLB],
    ArchiveCode.A1631: [FileKind.APPB],
    ArchiveCode.A1632: [FileKind.JPBIBL],
    ArchiveCode.A1634: [FileKind.APPB],
    ArchiveCode.A101: [FileKind.JPNTCE],
    ArchiveCode.A102: [FileKind.JPNTCE],
    ArchiveCode.A1131: [FileKind.JPNTCE],
    ArchiveCode.A1523: [FileKind.JPBIBL],
    ArchiveCode.A153: [FileKind.JPBIBL],
}

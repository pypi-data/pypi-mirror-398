from enum import Enum

class DocumentType(Enum):
    PATENT_APPLICATION_DOCS = 0
    SUBMISSION_DOCS = 1
    DISPATCHED_DOCS = 2
    RESPONSE_DOCS = 3
    AMENDMENT_DOCS = 4


class XSLType(Enum):
    PROCEDURE = 0
    HTML = 1
    XML = 2
 
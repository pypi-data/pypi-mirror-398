import re
from ..charset.config import CharsetConversionConfig as CCC


charset_settings = [
    CCC(re.compile('JPOXMLDOC01-(appb|jpbibl|jpflst|pkda|pkgh|jpfolb).xml'), 'Shift_JIS'),
    CCC(re.compile('.+-jpflst.xml', re.IGNORECASE), 'Shift_JIS'),
    CCC(re.compile('.+-jpmngt.xml', re.IGNORECASE), 'Shift_JIS'),
    CCC(re.compile('.+-jpntce.xml', re.IGNORECASE), 'Shift_JIS'),
    CCC(re.compile('.+[an]fm.xml', re.IGNORECASE), 'Shift_JIS'),
]

from pathlib import Path
import xml.etree.ElementTree as ET
from .finder import find_all_xml
from .kind import FileKind
from .finder import get_xml_name

kinds = [
    FileKind.APPB,
    FileKind.JPBIBL,
    FileKind.JPFLST,
    FileKind.PKDA,
    FileKind.PKGH,
    FileKind.JPFOLB,
    FileKind.JPMNGT,
    FileKind.JPNTCE,
    FileKind.PROCEDURE_PARAMS,
    FileKind.IMAGE_MAP,
    FileKind.METADATA,
    FileKind.OCR_TEXT,
]


def merge_xml(src_dir: Path, dst_dir: Path):
    """merge specified xml in src_dir into all.xml

    Args:
        src_dir (Path): path to directory containing the xml.
        dst_dir (Path): path to directory where all.xml is stored in.
    """
    root = ET.Element('files')
    xml = find_all_xml(src_dir, kinds)
    for x in xml:
        e = ET.Element('file', {'href': x.name})
        root.append(e)
    et = ET.ElementTree(root)
    dst_xml = dst_dir / get_xml_name(FileKind.MERGED)
    et.write(str(dst_xml), encoding='UTF-8', xml_declaration=True)

from pathlib import Path
import xml.etree.ElementTree as ET
from ..old.info import ArchiveInfo
from ..xml.finder import get_xml_name
from ..xml.kind import FileKind


def generate_metadata(archive_info: ArchiveInfo, dst_dir: Path):
    """generate meta data based on ArchiveInfo to xml.

    meta data contains
      Document ID
      Document code, such as A163, A101;
      Archive extension, such as JWX, JPC;
      Archive kind, such as AAA, AER, NNF;
      
    Args:
        archive_info (ArchiveInfo): _description_
        dst_dir (Path): _description_
    """
    dst_xml = dst_dir / get_xml_name(FileKind.METADATA)
    et = generate_metadata_etree(archive_info)
    et.write(str(dst_xml), encoding='UTF-8')


def generate_metadata_etree(archive_info: ArchiveInfo) -> ET.ElementTree:
    root = ET.Element('metadata')

    elem = ET.SubElement(root, 'id')
    elem.text = archive_info.id
    elem = ET.SubElement(root, 'archive')
    elem.text = archive_info.archive.name
    elem = ET.SubElement(root, 'procedure')
    elem.text = archive_info.procedure.name
    elem = ET.SubElement(root, 'kind')
    elem.text = archive_info.kind.name
    elem = ET.SubElement(root, 'ext')
    elem.text = archive_info.ext.name

    tree = ET.ElementTree(root)
    return tree

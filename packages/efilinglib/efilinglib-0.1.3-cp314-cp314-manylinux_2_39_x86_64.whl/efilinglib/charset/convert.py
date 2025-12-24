from pathlib import Path
import xml.etree.ElementTree as ET
from ..settings.charsets import charset_settings


def convert_charset(src_dir: Path, dst_dir: Path):
    """convert charset of xml files under src_dir to dst_dir.
    src_dir and dst_dir must be diffrent.
    
    Args:
        src_dir (Path): path to directory containing the xml files.
        dst_dir (Path): path to directory where the translated files are stored in.
    """
    src_xmls = src_dir.glob('*.xml')
    for xml in src_xmls:
        dst_xml = dst_dir / xml.name
        convert_xml_charset(xml, dst_xml)


def convert_xml_charset(src_xml_path: Path,  dst_xml_path: Path):
    """actually convert charset

    Args:
        src_xml_path (Path): path to file to be converted.
        dst_xml_path (Path): path to file to be stored.
    """
    for setting in charset_settings:
        if setting.patterns.match(src_xml_path.name):
            with src_xml_path.open('r', encoding=setting.src_encoding) as f:
                xml = ET.fromstring(f.read())
                et = ET.ElementTree(xml)
                et.write(str(dst_xml_path), setting.dst_encoding, True)
            break

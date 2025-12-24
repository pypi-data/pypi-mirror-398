import re
from pathlib import Path
from .kind import FileKind
from ..settings.xml import xml_file_patterns


def find_xml(src_dir: Path, kind: FileKind):
    """find a xml matching with XmlKind in specified directory.

    Args:
        src_dir (Path): src directory to be found
        kind (XmlKind): the kind of xml to be found

    Raises:
        ValueError: raise if the file matching with kind was not found.

    Returns:
        Path: xml path object matching with the kind.
    """
    for f in src_dir.iterdir():
        if not f.is_file():
            continue
        pattern = xml_file_patterns[kind]
        if type(pattern) is str and f.name == pattern:
            return f
        elif isinstance(pattern, re.Pattern) and pattern.match(f.name):
            return f
    else:
        return None


def find_all_xml(src_dir: Path, kinds: list[FileKind]) -> list[Path]:
    xml = []
    patterns = [xml_file_patterns[e] for e in kinds]
    for f in src_dir.glob('*.xml'):
        for pattern in patterns:
            if type(pattern) is str and f.name == pattern:
                xml.append(f)
            elif isinstance(pattern, re.Pattern) and pattern.match(f.name):
                xml.append(f)
    return xml


def get_xml_name(kind: FileKind):
    pattern = xml_file_patterns[kind]
    if type(pattern) is str:
        return pattern
    else:
        raise KeyError('no xml name found for ' + kind)


def get_kind(xml_name: str):
    for key, pattern in xml_file_patterns.items():
        if type(pattern) is str and xml_name == pattern:
            return key
        elif isinstance(pattern, re.Pattern) and pattern.match(xml_name):
            return key
    else:
        raise ValueError('unknown xml type: ' + xml_name)

import pytesseract
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
from ..old.info import ArchiveCode
from ..xml.translate import get_root_node_name
from ..settings.ocr import ocr_settings


def save_ocr_text(src_dir: Path, code: ArchiveCode):
    """generate text from images under src_dir to ocr-text.xml

    do ocr depends on the code with lookup ocr_settings

    Args:
        src_dir (Path): _description_
        code (ArchiveCode): _description_
    """
    root_node = get_root_node_name(src_dir, code)
    if code in ocr_settings:
        if root_node in ocr_settings[code]:
            lang = ocr_settings[code][root_node]['lang']
            pattern = ocr_settings[code][root_node]['pattern']
            do_ocr(src_dir, lang, pattern)


def do_ocr(src_dir: Path, lang: str, pattern: str):
    root = ET.Element('ocr-text')
    for f in sorted(src_dir.glob(pattern)):
        image = Image.open(str(f))
        text = pytesseract.image_to_string(image, lang)
        e = ET.Element('text', {'src-image': f.name})
        e.text = text
        root.append(e)
    et = ET.ElementTree(root)
    et.write(str(src_dir / 'ocr-text.xml'), 'UTF-8')

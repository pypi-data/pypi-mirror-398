import tempfile
from pathlib import Path
from sparrow.libs.archive.extract import extract_archive
from sparrow.libs.archive.info import ArchiveInfo
from sparrow.libs.image import convert_images
from sparrow.libs.charset import convert_charset, convert_xml_charset
from sparrow.libs.metadata import generate_metadata
from sparrow.libs.xml import translate_xml, merge_xml, XSLType
from sparrow.libs.ocr.ocr import save_ocr_text


def extract(archive_info: ArchiveInfo, dst_dir: Path):
    with tempfile.TemporaryDirectory() as temp_dir:
        t = Path(temp_dir)
        extract_archive(archive_info, t)
        convert_images(t, dst_dir)
        convert_charset(t, dst_dir)
        convert_xml_charset(archive_info.procedure,
                            dst_dir / archive_info.procedure.name)
        generate_metadata(archive_info, dst_dir)
        save_ocr_text(dst_dir, archive_info.code)
        translate_xml(dst_dir, dst_dir, archive_info.code, XSLType.PROCEDURE)
        merge_xml(dst_dir, dst_dir)
        translate_xml(dst_dir, dst_dir, archive_info.code, XSLType.HTML)
        translate_xml(dst_dir, dst_dir, archive_info.code, XSLType.XML)

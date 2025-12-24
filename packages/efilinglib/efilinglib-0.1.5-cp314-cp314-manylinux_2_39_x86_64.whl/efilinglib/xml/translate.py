import saxonche
import xml.etree.ElementTree as ET
from pathlib import Path
from .finder import find_xml, get_xml_name
from .filetypes import XSLType
from ..types.code import ArchiveCode
from ..settings.xml import xsl_config_set, code_to_main_file_kind
from ..xsl.finder import xsl_finder


def translate_xml(src_dir: Path, dst_dir: Path,
                  code: ArchiveCode, xsl_type: XSLType):
    """translate xml files to destination directory.
    
    the xml files under src_dir are translated to dst_dir.
    this translation is processed based on xsl_config_set
    with code and xsl_type parameters.

    code is ArchiveCode of the xml files.
    xsl_type is one of XSLType.PROCEDURE, XSLType.HTML, XSLType.XML

    this function must be called after some functions.
    
    -----------------------------------------------------
    info = ArchiveInfo('path/to/archive.JWX')

    # extract archive
    extract_archive(info, dst_dir)

    # convert charset of xml files to UTF-8. same src/dst directories
    convert_charset(dst_dir, dst_dir)

    # convert charset procedure xml to UTF-8.
    convert_xml_charset(archive_info.procedure,
        dst_dir / archive_info.procedure.name)

    # for generating image-map.xml
    convert_images(dst_dir, dst_dir)

    # for generating metadata.xml
    generate_metadata(archive_info, dst_dir)

    # for ocr-text.xml
    save_ocr_text(dst_dir, archive_info.code)

    # finally you can call translate_xml for generating xml from procedure xml.
    translate_xml(dst_dir, dst_dir, archive_info.code, XSLType.PROCEDURE)

    # some xml files are merged to all.xml
    merge_xml(dst_dir, dst_dir)

    # based on all.xml, translate to html and xml
    translate_xml(dst_dir, dst_dir, archive_info.code, XSLType.HTML)
    translate_xml(dst_dir, dst_dir, archive_info.code, XSLType.XML)
    -----------------------------------------------------

    Args:
        src_dir (Path): path to directory containing xml files.
        dst_dir (Path): path to directory where the translated files are stored in.
        code (ArchiveCode): ArchiveCode of the xml files. 
        xsl_type (XSLType): xsl_type is used for specify configuration in xsl_config_set.
            if XSLType.PROCEDURE is specified, procedure xml file is translated.
            if XSLType.HTML is specified, some html files are translated into dst_dir.
            if XSLType.XML is specified, some xml files are translated into dst_dir.
    """
    xsl_config = get_xsl_config_set(src_dir, code, xsl_type)
    for config in xsl_config:
        src_xml_path = str(find_xml(src_dir, config.src_kind))
        dst_filename = str(dst_dir / get_xml_name(config.dst_filename))
        xsl_path = str(xsl_finder(config.xsl_name))
        translate(src_xml_path, dst_filename, xsl_path)


def translate(src_xml_path: str, dst_filename: str, xsl_path: str):
    """translate xml by xsl using saxon

    Args:
        src_xml_path (str): path to xml file
        dst_filename (str): path to translated file
        xsl_path (str): path to xsl file
    """
    # Initialize the Saxon/C processor
    with saxonche.PySaxonProcessor(license=False) as proc:
        # Create an XSLT processor
        xslt_processor = proc.new_xslt30_processor()

        # Load the XML and XSLT files
        xml_file = proc.parse_xml(xml_file_name=src_xml_path)
        executable = xslt_processor.compile_stylesheet(
            stylesheet_file=xsl_path)

        # transformation
        executable.transform_to_file(
            xdm_node=xml_file, output_file=dst_filename)


def get_root_node_name(src_dir: Path, code: ArchiveCode):
    """find main xml file in src_dir and get root node of the file.

    Args:
        src_dir (Path): path to src_dir containing files extracted from the archive.
        code (ArchiveCode): archive code of the archive

    Returns:
        str: root node of the main xml.
    """
    kinds = code_to_main_file_kind[code]
    for kind in kinds:
        main_xml = find_xml(src_dir, kind)
        if main_xml is None:
            continue
        tree = ET.parse(str(main_xml))
        root = tree.getroot()
        if root.tag in xsl_config_set:
            return root.tag
    else:
        return None


def get_xsl_config_set(src_dir: Path, code: ArchiveCode, xsl_type: XSLType):
    """get xsl_config_set corresponding to xml files under src_dir

    Args:
        src_dir (Path): path to directory containing xml files
        code (ArchiveCode): Archive code of the xml files
        xsl_type (XSLType): one of XSLType.PROCEDURE, XSLType.HTML, XSLType.XML

    Returns:
        dict: xsl_config_set
    """
    root_tag = get_root_node_name(src_dir, code)
    if root_tag in xsl_config_set:
        return xsl_config_set[root_tag][xsl_type]
    else:
        return None


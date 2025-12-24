from itertools import chain
from pathlib import Path
from .config import ImageConversionConfig
from .converter import ImageConverter
from .kind import ImageKind
from .results import get_results_as_xml
from ..settings.image import image_settings
from ..xml.finder import get_xml_name
from ..xml.kind import FileKind


def convert_images(images_dir: Path, dst_dir: Path, with_image_map=True):
    """convert images using configuration

    *.tif and *.jpg under images_dir are resized and its file format are converted to dst_dir.
    the size and the format are configured in image_settings.

    Args:
        images_dir (Path): path to directory containing images.
        dst_dir (Path): path to directory where the images are converted to.
        with_image_map (bool, optional): output conversion log as xml. Defaults to True.
    """
    tiffs = images_dir.glob('*.tif')
    jpgs = images_dir.glob('*.jpg')
    images = chain(tiffs, jpgs)
    converters = create_converters(images, dst_dir, image_settings)
    results = [converter.convert() for converter in converters]

    if with_image_map:
        result = get_results_as_xml(results)
        result.write(
            str(dst_dir / get_xml_name(FileKind.IMAGE_MAP)), 'utf-8', True)


def create_converters(images: list[Path], dst_dir: Path, config: list[ImageConversionConfig]):
    """instantiate ImageConverter using config

    Args:
        images (list[Path]): _description_
        dst_dir (Path): _description_
        config (list[ImageConversionConfig]): _description_

    Returns:
        _type_: _description_
    """
    converters = []
    for image in images:
        kind = ImageKind.get_kind(str(image.stem))
        for c in config:
            if c.apply_to == 'all' or kind == c.apply_to:
                converters.append(ImageConverter(image, dst_dir, c))
    return converters

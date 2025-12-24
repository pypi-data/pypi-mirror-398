from importlib import resources
from pathlib import Path
from . import stylesheets


def xsl_finder(xsl_name: str) -> Path:
    xsl = resources.files(stylesheets) / xsl_name
    return xsl

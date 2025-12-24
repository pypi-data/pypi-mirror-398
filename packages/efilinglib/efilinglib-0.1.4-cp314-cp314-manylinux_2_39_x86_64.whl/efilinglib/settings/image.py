from ..image.config import ImageConversionConfig as ICC


image_settings = [
    ICC("all", "thumbnail", 300, 300, "-thumbnail", ".webp"),
    ICC("all", "middle", 600, 600,  "-middle",  ".webp"),
    ICC("all", "large", 800,  0, "-large", ".webp"),
]

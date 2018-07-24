from io import BytesIO

from PIL import Image

DEFAULT_OUTPUT_FORMAT = 'JPEG'


class BaseImageHandler:
    """Base class for all image handlers"""
    def __init__(self, data=None, image=None, format=None):
        self._image = image
        if image is None:
            try:
                self._image = Image.open(BytesIO(data))
            except OSError:
                self._image = None

        self._format = format
        if not format:
            self._format = DEFAULT_OUTPUT_FORMAT

    def _get_binary_image(self, image=None, format=None):
        """Returns image binary data"""
        if not image:
            image = self._image
        if not image:
            return

        if not format:
            format = self._format

        _file = BytesIO()
        image.save(_file, format=format)
        _file.seek(0)
        return _file.read()


class ImageFormatConverter(BaseImageHandler):
    """Converts images into another image format"""
    available_formats = {'PNG', 'JPEG', 'GIF'}

    def validate_format(self, img_format):
        return img_format.upper() in self.available_formats

    def convert_to(self, img_format):
        return self._get_binary_image(format=img_format.upper())


class ImageRotator(BaseImageHandler):
    """Rotates images by provided angle. In degrees counter clockwise"""

    def rotate(self, angle):
        image = self._image.rotate(int(angle))
        return self._get_binary_image(image=image)


class ImageResizingHandler(BaseImageHandler):
    """Resizes an image by height and width"""

    def resize(self, width, height):
        image = self._image.resize((int(width), int(height)))
        return self._get_binary_image(image=image)

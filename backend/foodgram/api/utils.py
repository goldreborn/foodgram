import base64

from django.core.files.base import ContentFile
from rest_framework.serializers import ImageField


class Base64ImageField(ImageField):
    """
    Поле для хранения изображений в формате Base64.

    Это поле позволяет хранить изображения в формате Base64,
    что полезно для передачи изображений через API.
    """

    def to_internal_value(self, data):
        """Метод to_internal_value преобразует строку Base64 в файл."""
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)

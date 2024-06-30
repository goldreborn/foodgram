"""
Модуль для вспомогательных функций и пользовательских полей.

Этот модуль предоставляет вспомогательные функции и пользовательские поля,
используемые в сериализаторах и моделях.
"""
import uuid
from django.core.files.base import ContentFile
from rest_framework import serializers

import base64


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            id = uuid.uuid4()
            data = ContentFile(base64.b64decode(imgstr), name=f"{id}.{ext}")
        return super().to_internal_value(data)

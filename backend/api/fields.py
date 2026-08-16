import base64
import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
    """Image field that accepts a base64-encoded data URI."""

    def to_internal_value(self, data):
        """Decode a base64 data URI into a file object."""
        if isinstance(data, str) and data.startswith('data:image'):
            image_format, image_str = data.split(';base64,')
            extension = image_format.split('/')[-1]
            file_uuid = uuid.uuid4()
            image_name = '{}.{}'.format(file_uuid, extension)
            data = ContentFile(
                base64.b64decode(image_str),
                name=image_name,
            )
        return super().to_internal_value(data)

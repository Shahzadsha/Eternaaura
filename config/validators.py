import os
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible


@deconstructible
class FileExtensionValidator:
    def __init__(self, allowed_extensions):
        self.allowed_extensions = [ext.lower() for ext in allowed_extensions]

    def __call__(self, value):
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in self.allowed_extensions:
            allowed_str = ", ".join(self.allowed_extensions)
            raise ValidationError(f"Unsupported file extension '{ext}'. Allowed extensions are: {allowed_str}")

    def __eq__(self, other):
        return isinstance(other, FileExtensionValidator) and self.allowed_extensions == other.allowed_extensions


@deconstructible
class MaxFileSizeValidator:
    def __init__(self, max_size_mb):
        self.max_size_mb = max_size_mb

    def __call__(self, value):
        if value.size > self.max_size_mb * 1024 * 1024:
            raise ValidationError(f"File size exceeds the maximum allowed limit of {self.max_size_mb} MB.")

    def __eq__(self, other):
        return isinstance(other, MaxFileSizeValidator) and self.max_size_mb == other.max_size_mb


validate_image_extension = FileExtensionValidator(['.jpg', '.jpeg', '.png', '.webp'])
validate_image_size = MaxFileSizeValidator(5)

validate_video_extension = FileExtensionValidator(['.mp4', '.webm', '.mov', '.avi'])
validate_video_size = MaxFileSizeValidator(50)

from django.core.exceptions import ValidationError


def file_size(value):
    limit = 5 * 1024 * 1024  # 5 MB
    if value.size > limit:
        raise ValidationError('File too large. Max 5 MB.')
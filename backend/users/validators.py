from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError

from . import constants


def validate_username(value):
    """Запрещает имя пользователя 'me'."""
    if value and value.lower() == "me":
        raise ValidationError(
            "Имя пользователя 'me' не разрешено"
        )
    if len(value) > constants.MAX_USERNAME_LENGTH:
        raise ValidationError(
            f"Имя пользователя не может быть длиннее "
            f"{constants.MAX_USERNAME_LENGTH} символов."
        )
    return value


username_validator = UnicodeUsernameValidator(
    message=(
        "Имя пользователя может содержать только буквы, цифры и "
        "@/./+/-/_"
    )
)

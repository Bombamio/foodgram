from django.contrib.auth.validators import UnicodeUsernameValidator


username_validator = UnicodeUsernameValidator(
    message=(
        "Имя пользователя может содержать только буквы, цифры и "
        "@/./+/-/_"
    )
)

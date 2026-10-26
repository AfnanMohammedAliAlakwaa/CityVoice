import re
import unicodedata

from django.core.exceptions import ValidationError


def normalize_phone(value):
    """
    يقبل رقمًا من 9 أرقام يبدأ بإحدى البدايات المحددة.
    يحوّل الأرقام العربية إلى إنجليزية.
    يسمح بترك رقم الهاتف فارغًا.
    """
    text = str(value or "").strip()
    normalized = ""

    for character in text:
        try:
            normalized += str(
                unicodedata.decimal(character)
            )
        except (ValueError, TypeError):
            normalized += character

    if normalized and not re.fullmatch(
        r"(?:77|71|78|73|70)[0-9]{7}",
        normalized,
    ):
        raise ValidationError(
            "أدخل رقم هاتف من 9 أرقام يبدأ بـ "
            "77 أو 71 أو 78 أو 73 أو 70."
        )

    return normalized
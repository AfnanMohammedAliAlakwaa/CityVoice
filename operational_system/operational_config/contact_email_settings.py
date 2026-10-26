import os
from pathlib import Path

from dotenv import load_dotenv


SYSTEM_DIRECTORY = Path(__file__).resolve().parent.parent

# قراءة إعدادات البيئة دون استبدال القيم الموجودة.
load_dotenv(
    SYSTEM_DIRECTORY / ".env",
    override=False,
)

load_dotenv(
    SYSTEM_DIRECTORY.parent / ".env",
    override=False,
)


# لا يُفعّل الإرسال إلا بعد تجهيز بريد المشروع.
CONTACT_EMAIL_ENABLED = (
    os.getenv(
        "CONTACT_EMAIL_ENABLED",
        "false",
    ).strip().lower()
    == "true"
)

# منع اعتبار رسائل الاختبار تحققًا حقيقيًا.
CONTACT_ALLOW_TEST_BACKEND = False


EMAIL_BACKEND = (
    "django.core.mail.backends.smtp.EmailBackend"
)

EMAIL_HOST = os.getenv(
    "EMAIL_HOST",
    "",
)

EMAIL_PORT = int(
    os.getenv(
        "EMAIL_PORT",
        "587",
    )
)

EMAIL_HOST_USER = os.getenv(
    "EMAIL_HOST_USER",
    "",
)

EMAIL_HOST_PASSWORD = os.getenv(
    "EMAIL_HOST_PASSWORD",
    "",
)

EMAIL_USE_TLS = (
    os.getenv(
        "EMAIL_USE_TLS",
        "true",
    ).strip().lower()
    == "true"
)

EMAIL_USE_SSL = (
    os.getenv(
        "EMAIL_USE_SSL",
        "false",
    ).strip().lower()
    == "true"
)

EMAIL_TIMEOUT = 12

DEFAULT_FROM_EMAIL = os.getenv(
    "DEFAULT_FROM_EMAIL",
    EMAIL_HOST_USER,
)
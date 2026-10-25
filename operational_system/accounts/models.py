from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        CITIZEN = "citizen", "مواطن"
        FIELD_WORKER = "field_worker", "عامل صيانة"
        MUNICIPAL_EMPLOYEE = "municipal_employee", "موظف البلدية"
        MUNICIPAL_MANAGER = "municipal_manager", "مدير البلدية"

    class Theme(models.TextChoices):
        LIGHT = "light", "فاتح"
        DARK = "dark", "داكن"

    role = models.CharField(
        max_length=30,
        choices=Role.choices,
        default=Role.CITIZEN,
    )

    phone_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="رقم الهاتف",
    )

    avatar = models.ImageField(
        upload_to="accounts/avatars/%Y/%m/",
        blank=True,
        verbose_name="الصورة الشخصية",
    )

    neighborhood_name = models.CharField(
        max_length=120,
        blank=True,
        verbose_name="الحي",
    )

    default_address = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="العنوان",
    )

    preferred_theme = models.CharField(
        max_length=10,
        choices=Theme.choices,
        default=Theme.LIGHT,
        verbose_name="المظهر",
    )

    def __str__(self):
        return self.username
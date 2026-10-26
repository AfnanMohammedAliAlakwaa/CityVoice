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

    verified_email = models.EmailField(
        blank=True,
        null=True,
        unique=True,
        editable=False,
    )

    email_verified_at = models.DateTimeField(
        blank=True,
        null=True,
        editable=False,
    )

    pending_email = models.EmailField(
        blank=True,
        editable=False,
    )

    @property
    def has_verified_contact(self):
        return bool(
            self.email_verified_at
            and self.verified_email
            and self.email
            and self.verified_email == self.email.strip().lower()
        )

    def __str__(self):
        return self.username


class EmailVerification(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="email_challenge",
    )

    target = models.EmailField(
        blank=True,
    )

    code_hash = models.CharField(
        max_length=256,
        blank=True,
    )

    expires_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    attempts = models.PositiveSmallIntegerField(
        default=0,
    )

    last_sent_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    window_started_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    send_count = models.PositiveSmallIntegerField(
        default=0,
    )

    blocked_until = models.DateTimeField(
        null=True,
        blank=True,
    )
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        CITIZEN = "citizen", "مواطن"
        FIELD_WORKER = "field_worker", "عامل صيانة"
        MUNICIPAL_EMPLOYEE = "municipal_employee", "موظف البلدية"
        MUNICIPAL_MANAGER = "municipal_manager", "مدير البلدية"

    role = models.CharField(
        max_length=30,
        choices=Role.choices,
        default=Role.CITIZEN,
    )

    phone_number = models.CharField(
        max_length=20,
        blank=True,
    )

    def __str__(self):
        return self.username
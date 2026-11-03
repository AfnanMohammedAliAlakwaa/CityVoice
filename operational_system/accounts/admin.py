from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (
            "معلومات CityVoice",
            {
                "fields": (
                    "role",
                    "worker_service",
                    "phone_number",
                )
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "معلومات CityVoice",
            {
                "fields": (
                    "role",
                    "worker_service",
                    "phone_number",
                )
            },
        ),
    )

    list_display = (
        "username",
        "email",
        "role",
        "worker_service",
        "is_staff",
        "is_active",
    )

    list_filter = (
        "role",
        "worker_service",
        "is_staff",
        "is_active",
    )
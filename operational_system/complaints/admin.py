from django.contrib.gis import admin

from .models import Complaint


@admin.register(Complaint)
class ComplaintAdmin(admin.GISModelAdmin):
    list_display = (
        "reference_number",
        "citizen",
        "service",
        "category",
        "status",
        "priority",
        "created_at",
    )

    list_filter = (
        "status",
        "priority",
        "service",
        "category",
        "created_at",
    )

    search_fields = (
        "reference_number",
        "description",
        "address",
        "citizen__username",
    )

    readonly_fields = (
        "reference_number",
        "created_at",
        "updated_at",
    )

    ordering = ("-created_at",)
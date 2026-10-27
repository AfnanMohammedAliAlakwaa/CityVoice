from django.contrib import admin

from .models import ComplaintFeedback


@admin.register(ComplaintFeedback)
class ComplaintFeedbackAdmin(admin.ModelAdmin):
    list_display = [
        "complaint_reference",
        "service_name",
        "rating",
        "created_at",
    ]

    list_filter = [
        "rating",
        "created_at",
    ]

    search_fields = [
        "complaint__reference_number",
        "complaint__citizen__username",
        "complaint__service__name_ar",
        "comment",
    ]

    readonly_fields = [
        "created_at",
        "updated_at",
    ]

    ordering = [
        "-created_at",
    ]

    @admin.display(
        description="رقم الشكوى",
        ordering="complaint__reference_number",
    )
    def complaint_reference(self, obj):
        return obj.complaint.reference_number

    @admin.display(
        description="الخدمة البلدية",
        ordering="complaint__service__name_ar",
    )
    def service_name(self, obj):
        return obj.complaint.service.name_ar
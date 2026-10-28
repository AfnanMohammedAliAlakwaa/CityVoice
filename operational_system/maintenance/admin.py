from django.contrib import admin

from complaints.models import Complaint

from .models import WorkOrder


@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = [
        "complaint",
        "assigned_to",
        "status",
        "scheduled_for",
        "created_at",
    ]

    list_filter = [
        "status",
        "scheduled_for",
        "created_at",
    ]

    search_fields = [
        "complaint__reference_number",
        "assigned_to__username",
        "assigned_to__first_name",
        "assigned_to__last_name",
        "instructions",
        "completion_notes",
    ]

    list_select_related = [
        "complaint",
        "assigned_to",
        "assigned_by",
    ]

    readonly_fields = [
        "accepted_at",
        "started_at",
        "completed_at",
        "created_at",
        "updated_at",
    ]

    fieldsets = [
        (
            "بيانات أمر العمل",
            {
                "fields": [
                    "complaint",
                    "assigned_to",
                    "assigned_by",
                    "status",
                    "scheduled_for",
                    "instructions",
                ]
            },
        ),
        (
            "تنفيذ المهمة",
            {
                "fields": [
                    "completion_notes",
                    "completion_photo",
                ]
            },
        ),
        (
            "التواريخ",
            {
                "fields": [
                    "accepted_at",
                    "started_at",
                    "completed_at",
                    "created_at",
                    "updated_at",
                ]
            },
        ),
    ]

    def save_model(self, request, obj, form, change):
        if (
            obj.assigned_by_id is None
            and request.user.role
            in ["municipal_employee", "municipal_manager"]
        ):
            obj.assigned_by = request.user

        super().save_model(request, obj, form, change)

        complaint_status = {
            WorkOrder.Status.ASSIGNED:
                Complaint.Status.ASSIGNED,
            WorkOrder.Status.ACCEPTED:
                Complaint.Status.ASSIGNED,
            WorkOrder.Status.IN_PROGRESS:
                Complaint.Status.IN_PROGRESS,
            WorkOrder.Status.COMPLETED:
                Complaint.Status.RESOLVED,
            WorkOrder.Status.CANCELLED:
                Complaint.Status.UNDER_REVIEW,
        }

        new_status = complaint_status.get(obj.status)

        if new_status and obj.complaint.status != new_status:
            obj.complaint.status = new_status
            obj.complaint.save(update_fields=["status", "updated_at"])
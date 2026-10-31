from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model

from complaints.models import Complaint

from .models import MaintenanceTeam, WorkOrder


class MaintenanceTeamAdminForm(forms.ModelForm):
    class Meta:
        model = MaintenanceTeam
        fields = "__all__"

    def clean_members(self):
        members = self.cleaned_data["members"]

        invalid_members = members.exclude(
            role="field_worker",
            is_active=True,
        )

        if invalid_members.exists():
            raise forms.ValidationError(
                "يجب أن تكون حسابات أعضاء الفريق "
                "نشطة وبدور عامل صيانة."
            )

        return members


@admin.register(MaintenanceTeam)
class MaintenanceTeamAdmin(admin.ModelAdmin):
    form = MaintenanceTeamAdminForm

    list_display = [
        "name",
        "service",
        "leader",
        "is_active",
        "created_at",
    ]

    list_filter = [
        "service",
        "is_active",
    ]

    search_fields = [
        "name",
        "service__name_ar",
        "leader__username",
        "leader__first_name",
        "leader__last_name",
    ]

    list_select_related = [
        "service",
        "leader",
    ]

    filter_horizontal = [
        "members",
    ]

    readonly_fields = [
        "created_at",
        "updated_at",
    ]

    fieldsets = [
        (
            "بيانات الفريق",
            {
                "fields": [
                    "name",
                    "service",
                    "is_active",
                ],
            },
        ),
        (
            "قائد الفريق والأعضاء",
            {
                "fields": [
                    "leader",
                    "members",
                ],
                "description": (
                    "اختر قائد الفريق، ثم أضف بقية أعضائه. "
                    "حسابات القائد والأعضاء يجب أن تكون "
                    "نشطة وبدور عامل صيانة."
                ),
            },
        ),
        (
            "التواريخ",
            {
                "fields": [
                    "created_at",
                    "updated_at",
                ],
            },
        ),
    ]


class WorkOrderAdminForm(forms.ModelForm):
    class Meta:
        model = WorkOrder
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()

        team = cleaned_data.get("team")
        assigned_to = cleaned_data.get("assigned_to")

        # فحص الإسناد الجديد أو تغييره دون تعطيل
        # عرض الأوامر القديمة إذا تغير قائد الفريق لاحقًا.
        assignment_changed = (
            not self.instance.pk
            or "team" in self.changed_data
            or "assigned_to" in self.changed_data
        )

        if team and assignment_changed:
            if not team.is_active:
                self.add_error(
                    "team",
                    "لا يمكن الإسناد إلى فريق غير نشط.",
                )

            if (
                not team.leader.is_active
                or team.leader.role != "field_worker"
            ):
                self.add_error(
                    "team",
                    "يجب أن يكون قائد الفريق "
                    "بحساب صيانة نشط.",
                )

            if assigned_to and assigned_to.pk != team.leader_id:
                self.add_error(
                    "assigned_to",
                    "اختر قائد الفريق المحدد "
                    "بوصفه مستلم أمر العمل.",
                )

        return cleaned_data


@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    form = WorkOrderAdminForm

    list_display = [
        "complaint",
        "team",
        "assigned_to",
        "status",
        "created_at",
    ]

    list_filter = [
        "status",
        "team",
        "created_at",
    ]

    search_fields = [
        "complaint__reference_number",
        "team__name",
        "assigned_to__username",
        "assigned_to__first_name",
        "assigned_to__last_name",
        "instructions",
        "completion_notes",
    ]

    list_select_related = [
        "complaint",
        "team",
        "team__leader",
        "assigned_to",
        "assigned_by",
        "accepted_by",
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
                    "team",
                    "assigned_to",
                    "assigned_by",
                    "status",
                    "instructions",
                ],
            },
        ),
        (
            "تنفيذ المهمة",
            {
                "fields": [
                    "accepted_by",
                    "completion_notes",
                    "completion_photo",
                ],
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
                ],
            },
        ),
    ]

    def formfield_for_foreignkey(
        self,
        db_field,
        request,
        **kwargs,
    ):
        if db_field.name == "assigned_by":
            User = get_user_model()

            kwargs["queryset"] = User.objects.filter(
                role__in=[
                    "municipal_employee",
                    "municipal_manager",
                ],
            )

        return super().formfield_for_foreignkey(
            db_field,
            request,
            **kwargs,
        )

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
            obj.complaint.save(
                update_fields=[
                    "status",
                    "updated_at",
                ],
            )
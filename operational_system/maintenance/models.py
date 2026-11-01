from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class WorkOrder(models.Model):
    class Status(models.TextChoices):
        ASSIGNED = "assigned", "تم الإسناد"
        ACCEPTED = "accepted", "تم قبول المهمة"
        IN_PROGRESS = "in_progress", "قيد التنفيذ"
        COMPLETED = "completed", "مكتمل"
        CANCELLED = "cancelled", "ملغي"

    complaint = models.OneToOneField(
        "complaints.Complaint",
        on_delete=models.CASCADE,
        related_name="work_order",
        verbose_name="البلاغ",
    )

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="assigned_work_orders",
        limit_choices_to={
            "role": "field_worker",
        },
        verbose_name="العامل الميداني",
    )

    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="issued_work_orders",
        limit_choices_to={
            "role__in": [
                "municipal_employee",
                "municipal_manager",
            ]
        },
        verbose_name="تم الإسناد بواسطة",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ASSIGNED,
        verbose_name="حالة أمر العمل",
    )

    instructions = models.TextField(
        blank=True,
        verbose_name="تعليمات التنفيذ",
    )

    scheduled_for = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="موعد التنفيذ",
    )

    accepted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="تاريخ قبول المهمة",
    )

    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="تاريخ بدء التنفيذ",
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="تاريخ إكمال المهمة",
    )

    completion_notes = models.TextField(
        blank=True,
        verbose_name="ملاحظات الإنجاز",
    )

    completion_photo = models.ImageField(
        upload_to="maintenance/completed/%Y/%m/",
        null=True,
        blank=True,
        verbose_name="صورة بعد الإنجاز",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ إنشاء أمر العمل",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخر تحديث",
    )

    def clean(self):
        super().clean()

        if (
            self.assigned_to_id
            and self.assigned_to.role != "field_worker"
        ):
            raise ValidationError(
                {
                    "assigned_to": (
                        "يجب إسناد أمر العمل إلى مستخدم "
                        "بدور عامل صيانة."
                    )
                }
            )

        if (
            self.assigned_by_id
            and self.assigned_by.role
            not in [
                "municipal_employee",
                "municipal_manager",
            ]
        ):
            raise ValidationError(
                {
                    "assigned_by": (
                        "يجب أن يكون مُصدر أمر العمل "
                        "موظفًا أو مديرًا بالبلدية."
                    )
                }
            )

        if (
            self.status == self.Status.COMPLETED
            and not self.completion_notes.strip()
        ):
            raise ValidationError(
                {
                    "completion_notes": (
                        "أضف ملاحظات الإنجاز قبل "
                        "إكمال أمر العمل."
                    )
                }
            )

    def save(self, *args, **kwargs):
        now = timezone.now()

        if (
            self.status == self.Status.ACCEPTED
            and self.accepted_at is None
        ):
            self.accepted_at = now

        if (
            self.status == self.Status.IN_PROGRESS
            and self.started_at is None
        ):
            self.started_at = now

        if (
            self.status == self.Status.COMPLETED
            and self.completed_at is None
        ):
            self.completed_at = now

        super().save(*args, **kwargs)

        complaint_status = None

        if self.status in [
            self.Status.ASSIGNED,
            self.Status.ACCEPTED,
        ]:
            complaint_status = "assigned"

        elif self.status == self.Status.IN_PROGRESS:
            complaint_status = "in_progress"

        elif self.status == self.Status.COMPLETED:
            complaint_status = "resolved"

        if (
            complaint_status
            and self.complaint.status != complaint_status
        ):
            self.complaint.status = complaint_status

            self.complaint.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

    def __str__(self):
        return (
            f"أمر عمل "
            f"{self.complaint.reference_number} "
            f"- {self.get_status_display()}"
        )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "أمر عمل"
        verbose_name_plural = "أوامر العمل"


class WorkOrderAssignmentHistory(models.Model):
    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.CASCADE,
        related_name="assignment_history",
        verbose_name="أمر العمل",
    )

    previous_assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="previous_work_order_assignments",
        limit_choices_to={
            "role": "field_worker",
        },
        verbose_name="قائد الفريق السابق",
    )

    new_assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="new_work_order_assignments",
        limit_choices_to={
            "role": "field_worker",
        },
        verbose_name="قائد الفريق الجديد",
    )

    reassigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="work_order_reassignments",
        limit_choices_to={
            "role__in": [
                "municipal_employee",
                "municipal_manager",
            ]
        },
        verbose_name="أعيد الإسناد بواسطة",
    )

    reason = models.TextField(
        verbose_name="سبب إعادة الإسناد",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ إعادة الإسناد",
    )

    def clean(self):
        super().clean()

        if (
            self.previous_assigned_to_id
            == self.new_assigned_to_id
        ):
            raise ValidationError(
                {
                    "new_assigned_to": (
                        "يجب اختيار قائد فريق مختلف."
                    )
                }
            )

    def __str__(self):
        return (
            f"{self.work_order} - "
            f"{self.previous_assigned_to} إلى "
            f"{self.new_assigned_to}"
        )

    class Meta:
        ordering = [
            "-created_at",
            "-pk",
        ]
        verbose_name = "سجل إعادة إسناد"
        verbose_name_plural = (
            "سجل إعادة إسناد أوامر العمل"
        )
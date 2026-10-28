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
        limit_choices_to={"role": "field_worker"},
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
                    "assigned_to":
                        "يجب إسناد أمر العمل إلى مستخدم بدور عامل صيانة."
                }
            )

        if (
            self.assigned_by_id
            and self.assigned_by.role
            not in ["municipal_employee", "municipal_manager"]
        ):
            raise ValidationError(
                {
                    "assigned_by":
                        "يجب أن يكون مُصدر أمر العمل موظفًا أو مديرًا بالبلدية."
                }
            )

        if (
            self.status == self.Status.COMPLETED
            and not self.completion_notes.strip()
        ):
            raise ValidationError(
                {
                    "completion_notes":
                        "أضف ملاحظات الإنجاز قبل إكمال أمر العمل."
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

    def __str__(self):
        return (
            f"أمر عمل {self.complaint.reference_number} "
            f"- {self.get_status_display()}"
        )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "أمر عمل"
        verbose_name_plural = "أوامر العمل"
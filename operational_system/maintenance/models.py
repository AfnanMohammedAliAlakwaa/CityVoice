from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class MaintenanceTeam(models.Model):
    name = models.CharField(
        max_length=150,
        unique=True,
        verbose_name="اسم الفريق",
    )

    service = models.ForeignKey(
        "municipal_services.MunicipalService",
        on_delete=models.PROTECT,
        related_name="maintenance_teams",
        verbose_name="الخدمة المختص بها الفريق",
    )

    leader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="led_maintenance_teams",
        limit_choices_to={
            "role": "field_worker",
            "is_active": True,
        },
        verbose_name="قائد الفريق",
    )

    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="maintenance_teams",
        blank=True,
        limit_choices_to={
            "role": "field_worker",
            "is_active": True,
        },
        verbose_name="أعضاء الفريق",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="الفريق نشط",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإنشاء",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخر تحديث",
    )

    def clean(self):
        super().clean()

        if self.leader_id:
            if (
                self.leader.role != "field_worker"
                or not self.leader.is_active
            ):
                raise ValidationError(
                    {
                        "leader": (
                            "اختر قائدًا بحساب صيانة نشط."
                        ),
                    }
                )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]
        verbose_name = "فريق صيانة"
        verbose_name_plural = "فرق الصيانة"


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

    team = models.ForeignKey(
        MaintenanceTeam,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="work_orders",
        verbose_name="فريق الصيانة",
    )

    # يبقى الحقل للتوافق مع الأوامر والواجهات الحالية.
    # عند ربط إسناد البلدية بالفريق سنضع فيه قائد الفريق.
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="assigned_work_orders",
        limit_choices_to={"role": "field_worker"},
        verbose_name="مستلم أمر العمل",
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
            ],
        },
        verbose_name="تم الإسناد بواسطة",
    )

    accepted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accepted_work_orders",
        limit_choices_to={"role": "field_worker"},
        verbose_name="تم قبول المهمة بواسطة",
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

    # يبقى للتوافق مع البيانات السابقة،
    # ولن نعرضه في نموذج الإسناد.
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

        errors = {}

        if self.assigned_to_id:
            if self.assigned_to.role != "field_worker":
                errors["assigned_to"] = (
                    "يجب أن يكون مستلم أمر العمل "
                    "مستخدمًا بدور عامل صيانة."
                )

        if self.assigned_by_id:
            if self.assigned_by.role not in {
                "municipal_employee",
                "municipal_manager",
            }:
                errors["assigned_by"] = (
                    "يجب أن يكون مُصدر أمر العمل "
                    "موظفًا أو مديرًا بالبلدية."
                )

        if self.team_id and self.complaint_id:
            if self.team.service_id != self.complaint.service_id:
                errors["team"] = (
                    "الفريق المحدد غير مختص بخدمة البلاغ."
                )

        if self.accepted_by_id:
            if self.accepted_by.role != "field_worker":
                errors["accepted_by"] = (
                    "يجب أن يكون من قبل المهمة "
                    "مستخدمًا بدور عامل صيانة."
                )

        if (
            self.status == self.Status.COMPLETED
            and not self.completion_photo
        ):
            errors["completion_photo"] = (
                "أرفق صورة الإنجاز قبل إكمال أمر العمل."
            )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        now = timezone.now()
        timestamp_fields = []

        if (
            self.status == self.Status.ACCEPTED
            and self.accepted_at is None
        ):
            self.accepted_at = now
            timestamp_fields.append("accepted_at")

        if (
            self.status == self.Status.IN_PROGRESS
            and self.started_at is None
        ):
            self.started_at = now
            timestamp_fields.append("started_at")

        if (
            self.status == self.Status.COMPLETED
            and self.completed_at is None
        ):
            self.completed_at = now
            timestamp_fields.append("completed_at")

        # تضمين الوقت التلقائي عند الحفظ بـ update_fields.
        update_fields = kwargs.get("update_fields")

        if update_fields is not None:
            if not update_fields:
                return

            kwargs["update_fields"] = set(update_fields) | set(
                timestamp_fields
            )

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
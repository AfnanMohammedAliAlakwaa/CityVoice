import uuid

from django.conf import settings
from django.contrib.gis.db import models
from django.utils import timezone


class Complaint(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "مُقدَّم"
        UNDER_REVIEW = "under_review", "قيد المراجعة"
        ASSIGNED = "assigned", "تم الإسناد"
        IN_PROGRESS = "in_progress", "قيد التنفيذ"
        RESOLVED = "resolved", "تم الحل"
        CLOSED = "closed", "مغلق"
        REJECTED = "rejected", "مرفوض"

    class Priority(models.TextChoices):
        LOW = "low", "منخفضة"
        MEDIUM = "medium", "متوسطة"
        HIGH = "high", "عالية"
        URGENT = "urgent", "عاجلة"

    reference_number = models.CharField(
        max_length=25,
        unique=True,
        editable=False,
        verbose_name="الرقم المرجعي",
    )

    citizen = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="complaints",
        verbose_name="المواطن",
    )

    service = models.ForeignKey(
        "municipal_services.MunicipalService",
        on_delete=models.PROTECT,
        related_name="complaints",
        verbose_name="الخدمة البلدية",
    )

    category = models.ForeignKey(
        "municipal_services.ServiceCategory",
        on_delete=models.PROTECT,
        related_name="complaints",
        verbose_name="تصنيف البلاغ",
    )

    asset = models.ForeignKey(
        "assets.MunicipalAsset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="complaints",
        verbose_name="الأصل المرتبط",
    )

    neighborhood = models.ForeignKey(
        "locations.Neighborhood",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="complaints",
        verbose_name="الحي",
    )

    description = models.TextField(
        verbose_name="وصف البلاغ",
    )

    photo = models.ImageField(
        upload_to="complaints/%Y/%m/",
        null=True,
        blank=True,
        verbose_name="صورة البلاغ",
    )

    location = models.PointField(
        srid=4326,
        verbose_name="موقع البلاغ",
    )

    address = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="العنوان",
    )

    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        verbose_name="الأولوية",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SUBMITTED,
        verbose_name="حالة البلاغ",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ التقديم",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخر تحديث",
    )

    def save(self, *args, **kwargs):
        if not self.reference_number:
            year = timezone.localdate().year
            short_code = uuid.uuid4().hex[:8].upper()

            self.reference_number = (
                f"CV-{year}-{short_code}"
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.reference_number}"
            f" - {self.get_status_display()}"
        )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "بلاغ"
        verbose_name_plural = "البلاغات"


class ComplaintHistory(models.Model):
    class Action(models.TextChoices):
        SUBMITTED = "submitted", "تقديم البلاغ"
        REVIEWED = "reviewed", "اعتماد المراجعة"
        UPDATED = "updated", "تعديل بيانات المراجعة"
        ASSIGNED = "assigned", "إسناد البلاغ"
        STATUS_CHANGED = "status_changed", "تغيير الحالة"

    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name="history",
        verbose_name="البلاغ",
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="complaint_history_actions",
        verbose_name="منفذ الإجراء",
    )

    actor_name = models.CharField(
        max_length=320,
        blank=True,
        verbose_name="اسم منفذ الإجراء وقت التسجيل",
    )

    action = models.CharField(
        max_length=30,
        choices=Action.choices,
        verbose_name="نوع الإجراء",
    )

    notes = models.TextField(
        blank=True,
        verbose_name="تفاصيل الإجراء",
    )

    changes = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="القيم قبل التعديل وبعده",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإجراء",
    )

    def save(self, *args, **kwargs):
        # حفظ الاسم وقت إنشاء السجل حتى يبقى
        # ظاهرًا إذا تغير الحساب أو حُذف لاحقًا.
        if self._state.adding and self.actor_id:
            full_name = self.actor.get_full_name().strip()
            username = self.actor.get_username()

            self.actor_name = (
                f"{full_name} — {username}"
                if full_name
                else username
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.complaint.reference_number}"
            f" - {self.get_action_display()}"
        )

    class Meta:
        ordering = ["-created_at", "-pk"]
        verbose_name = "إجراء على بلاغ"
        verbose_name_plural = "سجل إجراءات البلاغات"
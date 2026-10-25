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

    description = models.TextField(verbose_name="وصف البلاغ")

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
            self.reference_number = f"CV-{year}-{short_code}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference_number} - {self.get_status_display()}"

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "بلاغ"
        verbose_name_plural = "البلاغات"
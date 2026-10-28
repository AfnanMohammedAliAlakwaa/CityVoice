from django.conf import settings
from django.db import models


class Notification(models.Model):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="المستلم",
    )

    title = models.CharField(
        max_length=180,
        verbose_name="العنوان",
    )

    message = models.TextField(
        verbose_name="نص الإشعار",
    )

    link = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="الرابط",
    )

    is_read = models.BooleanField(
        default=False,
        verbose_name="تمت القراءة",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإنشاء",
    )

    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="تاريخ القراءة",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "إشعار"
        verbose_name_plural = "الإشعارات"

    def __str__(self):
        return f"{self.title} - {self.recipient}"
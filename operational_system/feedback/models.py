from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class ComplaintFeedback(models.Model):
    complaint = models.OneToOneField(
        "complaints.Complaint",
        on_delete=models.CASCADE,
        related_name="feedback",
        verbose_name="الشكوى",
    )

    rating = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5),
        ],
        verbose_name="التقييم",
        help_text="اختر تقييمًا من نجمة واحدة إلى خمس نجوم.",
    )

    comment = models.TextField(
        blank=True,
        max_length=1000,
        verbose_name="ملاحظات المواطن",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ التقييم",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخر تحديث",
    )

    def clean(self):
        super().clean()

        if not self.complaint_id:
            return

        allowed_statuses = [
            "resolved",
            "closed",
        ]

        if self.complaint.status not in allowed_statuses:
            raise ValidationError(
                {
                    "complaint": (
                        "لا يمكن تقييم الشكوى قبل اكتمال معالجتها."
                    )
                }
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"تقييم {self.complaint.reference_number} "
            f"- {self.rating} من 5"
        )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "تقييم شكوى"
        verbose_name_plural = "تقييمات الشكاوى"
from django.contrib.gis.db import models


class AssetType(models.Model):
    service = models.ForeignKey(
        "municipal_services.MunicipalService",
        on_delete=models.PROTECT,
        related_name="asset_types",
    )

    name_ar = models.CharField(
        max_length=100,
        verbose_name="نوع الأصل",
    )

    name_en = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="الاسم بالإنجليزية",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="نشط",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["service", "name_ar"]

        constraints = [
            models.UniqueConstraint(
                fields=["service", "name_ar"],
                name="unique_asset_type_per_service",
            )
        ]

    def __str__(self):
        return f"{self.name_ar} - {self.service.name_ar}"


class MunicipalAsset(models.Model):
    class Status(models.TextChoices):
        UNKNOWN = "unknown", "غير محدد"
        OPERATIONAL = "operational", "يعمل"
        NEEDS_MAINTENANCE = (
            "needs_maintenance",
            "يحتاج إلى صيانة",
        )
        UNDER_MAINTENANCE = (
            "under_maintenance",
            "تحت الصيانة",
        )
        OUT_OF_SERVICE = (
            "out_of_service",
            "خارج الخدمة",
        )

    class Condition(models.TextChoices):
        UNKNOWN = "unknown", "غير محددة"
        GOOD = "good", "جيدة"
        FAIR = "fair", "مقبولة"
        POOR = "poor", "سيئة"
        CRITICAL = "critical", "حرجة"

    asset_code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="رمز الأصل",
    )

    asset_type = models.ForeignKey(
        AssetType,
        on_delete=models.PROTECT,
        related_name="assets",
        verbose_name="نوع الأصل",
    )

    name_ar = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="اسم الأصل",
    )

    name_en = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="الاسم بالإنجليزية",
    )

    neighborhood = models.ForeignKey(
        "locations.Neighborhood",
        on_delete=models.PROTECT,
        related_name="assets",
        null=True,
        blank=True,
        verbose_name="الحي",
    )

    address = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="العنوان",
    )

    location = models.PointField(
        srid=4326,
        verbose_name="الموقع",
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.UNKNOWN,
    )

    condition = models.CharField(
        max_length=20,
        choices=Condition.choices,
        default=Condition.UNKNOWN,
    )

    installation_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="تاريخ التركيب",
    )

    last_maintenance_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="تاريخ آخر صيانة",
    )

    notes = models.TextField(
        blank=True,
        verbose_name="ملاحظات",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["asset_code"]

    def __str__(self):
        return (
            f"{self.asset_code} - "
            f"{self.asset_type.service.name_ar}"
        )
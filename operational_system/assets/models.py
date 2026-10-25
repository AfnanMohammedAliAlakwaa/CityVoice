from django.contrib.gis.db import models


class AssetType(models.Model):
    service = models.ForeignKey(
        "municipal_services.MunicipalService",
        on_delete=models.PROTECT,
        related_name="asset_types",
    )
    name_ar = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
        OPERATIONAL = "operational", "Operational"
        NEEDS_MAINTENANCE = "needs_maintenance", "Needs maintenance"
        UNDER_MAINTENANCE = "under_maintenance", "Under maintenance"
        OUT_OF_SERVICE = "out_of_service", "Out of service"

    class Condition(models.TextChoices):
        GOOD = "good", "Good"
        FAIR = "fair", "Fair"
        POOR = "poor", "Poor"
        CRITICAL = "critical", "Critical"

    asset_code = models.CharField(max_length=50, unique=True)
    asset_type = models.ForeignKey(
        AssetType,
        on_delete=models.PROTECT,
        related_name="assets",
    )
    name_ar = models.CharField(max_length=150, blank=True)
    name_en = models.CharField(max_length=150, blank=True)
    neighborhood = models.ForeignKey(
        "locations.Neighborhood",
        on_delete=models.PROTECT,
        related_name="assets",
        null=True,
        blank=True,
    )
    address = models.CharField(max_length=255, blank=True)
    location = models.PointField(srid=4326)
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.OPERATIONAL,
    )
    condition = models.CharField(
        max_length=20,
        choices=Condition.choices,
        default=Condition.GOOD,
    )
    installation_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["asset_code"]

    def __str__(self):
        return f"{self.asset_code} - {self.asset_type.name_ar}"
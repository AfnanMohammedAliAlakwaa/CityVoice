from django.contrib.gis.db import models


class District(models.Model):
    name_ar = models.CharField(max_length=100, unique=True)
    name_en = models.CharField(max_length=100, blank=True)
    boundary = models.MultiPolygonField(
        srid=4326,
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name_ar"]

    def __str__(self):
        return self.name_ar


class Neighborhood(models.Model):
    district = models.ForeignKey(
        District,
        on_delete=models.PROTECT,
        related_name="neighborhoods",
    )
    name_ar = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100, blank=True)
    boundary = models.MultiPolygonField(
        srid=4326,
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["district", "name_ar"]
        constraints = [
            models.UniqueConstraint(
                fields=["district", "name_ar"],
                name="unique_neighborhood_per_district",
            )
        ]

    def __str__(self):
        return f"{self.name_ar} - {self.district.name_ar}"
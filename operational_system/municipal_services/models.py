from django.db import models


class MunicipalService(models.Model):
    name_ar = models.CharField(max_length=100, unique=True)
    name_en = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name_ar"]

    def __str__(self):
        return self.name_ar


class ServiceCategory(models.Model):
    service = models.ForeignKey(
        MunicipalService,
        on_delete=models.PROTECT,
        related_name="categories",
    )
    name_ar = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["service", "name_ar"]
        constraints = [
            models.UniqueConstraint(
                fields=["service", "name_ar"],
                name="unique_category_per_service",
            )
        ]

    def __str__(self):
        return f"{self.name_ar} - {self.service.name_ar}"
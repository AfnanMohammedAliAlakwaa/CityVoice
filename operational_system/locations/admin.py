from django.contrib.gis import admin

from .models import District, Neighborhood


@admin.register(District)
class DistrictAdmin(admin.GISModelAdmin):
    list_display = ("name_ar", "name_en", "is_active", "updated_at")
    search_fields = ("name_ar", "name_en")
    list_filter = ("is_active",)


@admin.register(Neighborhood)
class NeighborhoodAdmin(admin.GISModelAdmin):
    list_display = (
        "name_ar",
        "name_en",
        "district",
        "is_active",
        "updated_at",
    )
    search_fields = ("name_ar", "name_en", "district__name_ar")
    list_filter = ("district", "is_active")
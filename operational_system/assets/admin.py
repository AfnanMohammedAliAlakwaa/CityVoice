from django.contrib.gis import admin

from .models import AssetType, MunicipalAsset


@admin.register(AssetType)
class AssetTypeAdmin(admin.ModelAdmin):
    list_display = (
        "name_ar",
        "name_en",
        "service",
        "is_active",
        "updated_at",
    )
    list_filter = ("service", "is_active")
    search_fields = ("name_ar", "name_en", "service__name_ar")
    list_select_related = ("service",)


@admin.register(MunicipalAsset)
class MunicipalAssetAdmin(admin.GISModelAdmin):
    list_display = (
        "asset_code",
        "asset_type",
        "status",
        "condition",
        "neighborhood",
        "updated_at",
    )
    list_filter = (
        "asset_type",
        "status",
        "condition",
        "neighborhood",
    )
    search_fields = (
        "asset_code",
        "name_ar",
        "name_en",
        "address",
        "asset_type__name_ar",
    )
    list_select_related = ("asset_type", "neighborhood")
    readonly_fields = ("created_at", "updated_at")
from django.contrib import admin

from .models import MunicipalService, ServiceCategory


class ServiceCategoryInline(admin.TabularInline):
    model = ServiceCategory
    extra = 1


@admin.register(MunicipalService)
class MunicipalServiceAdmin(admin.ModelAdmin):
    list_display = ("name_ar", "name_en", "is_active", "updated_at")
    search_fields = ("name_ar", "name_en")
    list_filter = ("is_active",)
    inlines = (ServiceCategoryInline,)


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "name_ar",
        "name_en",
        "service",
        "is_active",
        "updated_at",
    )
    search_fields = ("name_ar", "name_en", "service__name_ar")
    list_filter = ("service", "is_active")
    list_select_related = ("service",)
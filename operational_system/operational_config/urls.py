from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),

    path(
        "locations/",
        include("locations.urls"),
    ),

    path(
        "feedback/",
        include("feedback.urls"),
    ),

    path(
        "",
        include("citizen_portal.urls"),
    ),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
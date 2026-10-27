from django.urls import path

from . import views


app_name = "locations"


urlpatterns = [
    path(
        "main-boundary/",
        views.main_boundary,
        name="main_boundary",
    ),
]
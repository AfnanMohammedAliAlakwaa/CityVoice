from django.urls import path

from . import views


app_name = "accounts"


urlpatterns = [
    path(
        "avatar/update/",
        views.update_avatar,
        name="update_avatar",
    ),
]
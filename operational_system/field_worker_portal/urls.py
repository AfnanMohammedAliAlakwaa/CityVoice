from django.urls import path

from . import views


app_name = "field_worker_portal"


urlpatterns = [
    path("login/", views.worker_login, name="login"),
    path("logout/", views.worker_logout, name="logout"),
    path("", views.dashboard, name="dashboard"),
]

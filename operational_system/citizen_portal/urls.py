from django.urls import path

from . import views


app_name = "citizen_portal"

urlpatterns = [
    path(
        "complaints/new/",
        views.submit_complaint,
        name="submit_complaint",
    ),
    path(
        "complaints/success/<str:reference_number>/",
        views.complaint_success,
        name="complaint_success",
    ),
    path(
        "categories/",
        views.load_categories,
        name="load_categories",
    ),
]
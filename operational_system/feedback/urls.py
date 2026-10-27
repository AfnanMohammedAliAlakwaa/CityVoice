from django.urls import path

from . import views


app_name = "feedback"


urlpatterns = [
    path(
        "",
        views.feedback_list,
        name="feedback_list",
    ),
    path(
        "rate/<str:reference_number>/",
        views.submit_feedback,
        name="submit_feedback",
    ),
    path(
        "success/<str:reference_number>/",
        views.feedback_success,
        name="feedback_success",
    ),
]
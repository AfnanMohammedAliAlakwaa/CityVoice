from django.urls import path

from . import (
    preference_views,
    verification_views,
    views,
)


app_name = "citizen_portal"


urlpatterns = [
    path(
        "login/",
        views.citizen_auth,
        name="auth",
    ),
    path(
        "logout/",
        views.citizen_logout,
        name="logout",
    ),
    path(
        "verify-contact/",
        verification_views.verify_contact,
        name="verify_contact",
    ),
    path(
        "verify-contact/sent/",
        verification_views.verify_contact,
        name="verify_contact_sent",
    ),
    path(
        "",
        views.home,
        name="home",
    ),
    path(
        "my-complaints/",
        views.complaint_list,
        name="complaint_list",
    ),
    path(
        "my-complaints/<str:reference_number>/",
        views.complaint_detail,
        name="complaint_detail",
    ),
    path(
        "my-account/",
        views.account,
        name="account",
    ),
    path(
        "my-account/saved/",
        views.account_saved,
        name="account_saved",
    ),
    path(
        "my-account/theme/",
        preference_views.save_theme,
        name="save_theme",
    ),
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
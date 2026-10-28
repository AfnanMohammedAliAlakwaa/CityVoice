from django.urls import path

from . import views


app_name = "municipal_portal"


urlpatterns = [
    path(
        "",
        views.dashboard,
        name="dashboard",
    ),

    path(
        "services-assets/",
        views.services_assets,
        name="services_assets",
    ),

    path(
        "notifications/",
        views.notification_list,
        name="notification_list",
    ),

    path(
        "notifications/read-all/",
        views.mark_all_notifications_read,
        name="mark_all_notifications_read",
    ),

    path(
        "notifications/<int:notification_id>/read/",
        views.mark_notification_read,
        name="mark_notification_read",
    ),

    path(
        "complaints/",
        views.complaint_list,
        name="complaint_list",
    ),

    path(
        "complaints/<str:reference_number>/",
        views.complaint_detail,
        name="complaint_detail",
    ),

    path(
        "work-orders/",
        views.work_order_list,
        name="work_order_list",
    ),

    path(
        "workers/",
        views.worker_list,
        name="worker_list",
    ),
]
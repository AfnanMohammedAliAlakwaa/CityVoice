from django.urls import path

from . import complaint_views, notification_views, views


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
        "services-assets/add/",
        views.asset_create,
        name="asset_create",
    ),
    path(
        "services-assets/import/",
        views.asset_import,
        name="asset_import",
    ),
    path(
        "services-assets/template/",
        views.asset_excel_template,
        name="asset_excel_template",
    ),
    path(
        "notifications/",
        views.notification_list,
        name="notification_list",
    ),
    path(
        "notifications/summary/",
        notification_views.notification_summary,
        name="notification_summary",
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
        complaint_views.complaint_detail,
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
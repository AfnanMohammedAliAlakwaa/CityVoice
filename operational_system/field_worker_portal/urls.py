from django.urls import path

from . import views


app_name = "field_worker_portal"


urlpatterns = [
    path(
        "login/",
        views.worker_login,
        name="login",
    ),
    path(
        "logout/",
        views.worker_logout,
        name="logout",
    ),
    path(
        "",
        views.dashboard,
        name="dashboard",
    ),
    path(
        "tasks/<int:order_id>/",
        views.task_detail,
        name="task_detail",
    ),
    path(
        "tasks/<int:order_id>/accept/",
        views.accept_task,
        name="accept_task",
    ),
    path(
        "tasks/<int:order_id>/start/",
        views.start_task,
        name="start_task",
    ),
    path(
        "tasks/<int:order_id>/complete/",
        views.complete_task,
        name="complete_task",
    ),
]
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
    "account/",
    views.account,
    name="account",
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
        "tasks/",
        views.tasks,
        name="tasks",
    ),
    path(
    "notifications/",
    views.notifications,
    name="notifications",
),
    path(
    "achievements/",
    views.achievements,
    name="achievements",
),
    path(
    "achievements/<int:order_id>/",
    views.achievement_detail,
    name="achievement_detail",
),
    path(
    "tasks/",
    views.task_list,
    name="task_list",
),
        path(
        "tasks/<int:order_id>/completion/success/",
        views.completion_success,
        name="completion_success",
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
    "tasks/<int:order_id>/completion/",
    views.complete_task,
    name="complete_task",
),
]
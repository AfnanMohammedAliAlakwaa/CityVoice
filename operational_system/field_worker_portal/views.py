from functools import wraps

from django.contrib.auth import (
    login as auth_login,
    logout as auth_logout,
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import (
    require_http_methods,
    require_POST,
)

from maintenance.models import MaintenanceTeam, WorkOrder


def is_field_worker(user):
    return (
        user.is_authenticated
        and user.is_active
        and user.role == "field_worker"
    )


def field_worker_required(view_function):
    """السماح لحسابات الصيانة النشطة فقط."""

    @wraps(view_function)
    @login_required(login_url="field_worker_portal:login")
    def wrapped_view(request, *args, **kwargs):
        if not is_field_worker(request.user):
            raise PermissionDenied(
                "هذه الصفحة مخصصة لحسابات الصيانة النشطة."
            )

        return view_function(request, *args, **kwargs)

    return wrapped_view


def worker_teams(user):
    """
    القائد محسوب ضمن فريقه حتى لو لم يُضف
    مرة أخرى إلى قائمة الأعضاء.
    """

    return (
        MaintenanceTeam.objects.filter(
            Q(leader=user) | Q(members=user)
        )
        .select_related(
            "service",
            "leader",
        )
        .distinct()
        .order_by("name")
    )


def worker_work_orders(user):
    """إظهار أوامر فرق المستخدم فقط."""

    team_ids = worker_teams(user).values("pk")

    return (
        WorkOrder.objects.filter(
            team_id__in=team_ids,
        )
        .select_related(
            "team",
            "team__leader",
            "assigned_to",
            "assigned_by",
            "accepted_by",
            "complaint",
            "complaint__service",
            "complaint__category",
            "complaint__asset",
            "complaint__neighborhood",
        )
        .order_by("-created_at", "-pk")
    )


@never_cache
@require_http_methods(["GET", "POST"])
def worker_login(request):
    if is_field_worker(request.user):
        return redirect("field_worker_portal:home")

    form = AuthenticationForm(
        request=request,
        data=(
            request.POST
            if request.method == "POST"
            else None
        ),
    )

    form.fields["username"].label = "اسم المستخدم"
    form.fields["password"].label = "كلمة المرور"

    form.fields["username"].widget.attrs.update(
        {
            "class": "fw-input",
            "placeholder": "أدخل اسم المستخدم",
            "autocomplete": "username",
            "autocapitalize": "none",
            "spellcheck": "false",
        }
    )

    form.fields["password"].widget.attrs.update(
        {
            "class": "fw-input",
            "placeholder": "أدخل كلمة المرور",
            "autocomplete": "current-password",
        }
    )

    if request.method == "POST" and form.is_valid():
        user = form.get_user()

        if not is_field_worker(user):
            form.add_error(
                None,
                "هذا الحساب غير مخصص لتطبيق الصيانة.",
            )

        else:
            auth_login(request, user)

            return redirect(
                "field_worker_portal:home"
            )

    return render(
        request,
        "field_worker_portal/login.html",
        {
            "form": form,
        },
    )


@never_cache
@field_worker_required
@require_POST
def worker_logout(request):
    auth_logout(request)

    return redirect(
        "field_worker_portal:login"
    )


@never_cache
@field_worker_required
@require_http_methods(["GET"])
def home(request):
    teams = worker_teams(request.user)
    all_orders = worker_work_orders(request.user)

    stats = all_orders.aggregate(
        total_count=Count("pk"),
        new_count=Count(
            "pk",
            filter=Q(
                status=WorkOrder.Status.ASSIGNED,
            ),
        ),
        accepted_count=Count(
            "pk",
            filter=Q(
                status=WorkOrder.Status.ACCEPTED,
            ),
        ),
        in_progress_count=Count(
            "pk",
            filter=Q(
                status=WorkOrder.Status.IN_PROGRESS,
            ),
        ),
        completed_count=Count(
            "pk",
            filter=Q(
                status=WorkOrder.Status.COMPLETED,
            ),
        ),
    )

    selected_status = request.GET.get(
        "status",
        "",
    ).strip()

    valid_statuses = {
        value
        for value, label in WorkOrder.Status.choices
    }

    if selected_status not in valid_statuses:
        selected_status = ""

    search_query = request.GET.get(
        "q",
        "",
    ).strip()[:200]

    orders = all_orders

    if selected_status:
        orders = orders.filter(
            status=selected_status,
        )

    if search_query:
        orders = orders.filter(
            Q(
                complaint__reference_number__icontains=search_query
            )
            | Q(
                complaint__service__name_ar__icontains=search_query
            )
            | Q(
                complaint__category__name_ar__icontains=search_query
            )
            | Q(
                complaint__address__icontains=search_query
            )
            | Q(
                team__name__icontains=search_query
            )
        )

    paginator = Paginator(orders, 10)

    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    pagination_query = request.GET.copy()
    pagination_query.pop("page", None)

    return render(
        request,
        "field_worker_portal/home.html",
        {
            "teams": teams,
            "has_team": teams.exists(),
            "page_obj": page_obj,
            "work_orders": page_obj.object_list,
            "stats": stats,
            "status_choices": WorkOrder.Status.choices,
            "selected_status": selected_status,
            "search_query": search_query,
            "pagination_query": pagination_query.urlencode(),
        },
    )
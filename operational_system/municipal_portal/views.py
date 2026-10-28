from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from assets.models import MunicipalAsset
from complaints.models import Complaint
from maintenance.models import WorkOrder
from municipal_services.models import MunicipalService
from notifications.models import Notification

from .decorators import municipal_required


User = get_user_model()


@municipal_required
def dashboard(request):
    complaints = Complaint.objects.all()

    recent_complaints = (
        complaints
        .select_related(
            "citizen",
            "service",
            "category",
            "neighborhood",
        )
        .order_by("-created_at")[:8]
    )

    context = {
        "total_count": complaints.count(),

        "submitted_count": complaints.filter(
            status=Complaint.Status.SUBMITTED,
        ).count(),

        "under_review_count": complaints.filter(
            status=Complaint.Status.UNDER_REVIEW,
        ).count(),

        "assigned_count": complaints.filter(
            status=Complaint.Status.ASSIGNED,
        ).count(),

        "in_progress_count": complaints.filter(
            status=Complaint.Status.IN_PROGRESS,
        ).count(),

        "resolved_count": complaints.filter(
            status=Complaint.Status.RESOLVED,
        ).count(),

        "closed_count": complaints.filter(
            status=Complaint.Status.CLOSED,
        ).count(),

        "active_work_orders_count": (
            WorkOrder.objects
            .exclude(
                status__in=[
                    WorkOrder.Status.COMPLETED,
                    WorkOrder.Status.CANCELLED,
                ]
            )
            .count()
        ),

        "recent_complaints": recent_complaints,
    }

    return render(
        request,
        "municipal_portal/dashboard.html",
        context,
    )


@municipal_required
def services_assets(request):
    services = (
        MunicipalService.objects
        .prefetch_related("categories")
        .annotate(
            category_count=Count(
                "categories",
                distinct=True,
            ),
            asset_type_count=Count(
                "asset_types",
                distinct=True,
            ),
            asset_count=Count(
                "asset_types__assets",
                distinct=True,
            ),
        )
        .order_by("name_ar")
    )

    assets = (
        MunicipalAsset.objects
        .select_related(
            "asset_type",
            "asset_type__service",
            "neighborhood",
        )
        .order_by("-created_at")
    )

    return render(
        request,
        "municipal_portal/services_assets.html",
        {
            "services": services,
            "assets": assets,
        },
    )


@municipal_required
def complaint_list(request):
    complaints = Complaint.objects.select_related(
        "citizen",
        "service",
        "category",
        "neighborhood",
    )

    search_query = request.GET.get(
        "q",
        "",
    ).strip()

    selected_status = request.GET.get(
        "status",
        "",
    ).strip()

    selected_priority = request.GET.get(
        "priority",
        "",
    ).strip()

    selected_service = request.GET.get(
        "service",
        "",
    ).strip()

    if search_query:
        complaints = complaints.filter(
            Q(
                reference_number__icontains=search_query,
            )
            | Q(
                description__icontains=search_query,
            )
            | Q(
                address__icontains=search_query,
            )
            | Q(
                citizen__username__icontains=search_query,
            )
            | Q(
                citizen__first_name__icontains=search_query,
            )
            | Q(
                citizen__last_name__icontains=search_query,
            )
            | Q(
                service__name_ar__icontains=search_query,
            )
            | Q(
                category__name_ar__icontains=search_query,
            )
        )

    if selected_status:
        complaints = complaints.filter(
            status=selected_status,
        )

    if selected_priority:
        complaints = complaints.filter(
            priority=selected_priority,
        )

    if selected_service:
        complaints = complaints.filter(
            service_id=selected_service,
        )

    context = {
        "complaints": complaints.order_by("-created_at"),

        "services": (
            MunicipalService.objects
            .all()
            .order_by("name_ar")
        ),

        "status_choices": Complaint.Status.choices,
        "priority_choices": Complaint.Priority.choices,

        "search_query": search_query,
        "selected_status": selected_status,
        "selected_priority": selected_priority,
        "selected_service": selected_service,
    }

    return render(
        request,
        "municipal_portal/complaints/list.html",
        context,
    )


@municipal_required
def complaint_detail(request, reference_number):
    complaint = get_object_or_404(
        Complaint.objects.select_related(
            "citizen",
            "service",
            "category",
            "asset",
            "neighborhood",
        ),
        reference_number=reference_number,
    )

    try:
        work_order = complaint.work_order
    except WorkOrder.DoesNotExist:
        work_order = None

    context = {
        "complaint": complaint,
        "work_order": work_order,
        "maptiler_api_key": settings.MAPTILER_API_KEY,
    }

    return render(
        request,
        "municipal_portal/complaints/detail.html",
        context,
    )


@municipal_required
def work_order_list(request):
    work_orders = WorkOrder.objects.select_related(
        "complaint",
        "complaint__service",
        "assigned_to",
        "assigned_by",
    )

    search_query = request.GET.get(
        "q",
        "",
    ).strip()

    selected_status = request.GET.get(
        "status",
        "",
    ).strip()

    if search_query:
        work_orders = work_orders.filter(
            Q(
                complaint__reference_number__icontains=
                search_query
            )
            | Q(
                assigned_to__username__icontains=
                search_query
            )
            | Q(
                assigned_to__first_name__icontains=
                search_query
            )
            | Q(
                assigned_to__last_name__icontains=
                search_query
            )
            | Q(
                instructions__icontains=search_query
            )
        )

    if selected_status:
        work_orders = work_orders.filter(
            status=selected_status,
        )

    context = {
        "work_orders": work_orders.order_by(
            "-created_at",
        ),

        "status_choices": WorkOrder.Status.choices,
        "search_query": search_query,
        "selected_status": selected_status,
    }

    return render(
        request,
        "municipal_portal/work_orders/list.html",
        context,
    )


@municipal_required
def worker_list(request):
    workers = (
        User.objects
        .filter(
            role=User.Role.FIELD_WORKER,
            is_active=True,
        )
        .annotate(
            total_orders=Count(
                "assigned_work_orders",
                distinct=True,
            )
        )
        .order_by(
            "first_name",
            "last_name",
            "username",
        )
    )

    return render(
        request,
        "municipal_portal/workers/list.html",
        {
            "workers": workers,
        },
    )


@municipal_required
def notification_list(request):
    notifications = (
        Notification.objects
        .filter(
            recipient=request.user,
        )
        .order_by("-created_at")
    )

    return render(
        request,
        "municipal_portal/notifications.html",
        {
            "notifications": notifications,
        },
    )


@municipal_required
@require_POST
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(
        Notification,
        pk=notification_id,
        recipient=request.user,
    )

    if not notification.is_read:
        notification.is_read = True
        notification.read_at = timezone.now()

        notification.save(
            update_fields=[
                "is_read",
                "read_at",
            ]
        )

    if notification.link:
        return redirect(notification.link)

    return redirect(
        "municipal_portal:notification_list",
    )


@municipal_required
@require_POST
def mark_all_notifications_read(request):
    Notification.objects.filter(
        recipient=request.user,
        is_read=False,
    ).update(
        is_read=True,
        read_at=timezone.now(),
    )

    messages.success(
        request,
        "تم تحديد جميع الإشعارات كمقروءة.",
    )

    return redirect(
        "municipal_portal:notification_list",
    )
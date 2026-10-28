from datetime import date, datetime
from io import BytesIO

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.db import transaction
from django.db.models import Count, OuterRef, Q, Subquery
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from openpyxl import Workbook, load_workbook

from assets.models import AssetType, MunicipalAsset
from complaints.models import Complaint
from locations.models import Neighborhood
from maintenance.models import WorkOrder
from municipal_services.models import MunicipalService
from notifications.models import Notification

from .decorators import municipal_required
from .forms import AssetExcelUploadForm, MunicipalAssetForm


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

    last_completed_maintenance = (
        WorkOrder.objects
        .filter(
            complaint__asset=OuterRef("pk"),
            status=WorkOrder.Status.COMPLETED,
            completed_at__isnull=False,
        )
        .order_by("-completed_at")
        .values("completed_at")[:1]
    )

    assets = (
        MunicipalAsset.objects
        .select_related(
            "asset_type",
            "asset_type__service",
            "neighborhood",
        )
        .annotate(
            last_maintenance_at=Subquery(
                last_completed_maintenance,
            )
        )
        .order_by(
            "asset_type__service__name_ar",
            "asset_code",
        )
    )
    assets_by_service = {}

    for asset in assets:
        service_id = asset.asset_type.service_id

        assets_by_service.setdefault(
            service_id,
            [],
        ).append(asset)

    service_sections = []

    for service in services:
        service_sections.append(
            {
                "service": service,
                "assets": assets_by_service.get(
                    service.pk,
                    [],
                ),
            }
        )

    return render(
        request,
        "municipal_portal/services_assets.html",
        {
            "services": services,
            "assets": assets,
            "service_sections": service_sections,
            "asset_form": MunicipalAssetForm(),
            "excel_form": AssetExcelUploadForm(),
        },
    )

@municipal_required
@require_POST
def asset_create(request):
    form = MunicipalAssetForm(
        request.POST,
    )

    if form.is_valid():
        asset = form.save()

        messages.success(
            request,
            (
                f"تمت إضافة الأصل "
                f"{asset.asset_code} بنجاح."
            ),
        )

        return redirect(
            "municipal_portal:services_assets",
        )

    error_messages = []

    for field_errors in form.errors.values():
        for error in field_errors:
            error_messages.append(str(error))

    messages.error(
        request,
        "تعذر إضافة الأصل: "
        + "، ".join(error_messages),
    )

    return redirect(
        "municipal_portal:services_assets",
    )


@municipal_required
@require_POST
def asset_create(request):
    form = MunicipalAssetForm(
        request.POST,
    )

    if form.is_valid():
        asset = form.save()

        messages.success(
            request,
            (
                f"تمت إضافة الأصل "
                f"{asset.asset_code} بنجاح."
            ),
        )

        return redirect(
            "municipal_portal:services_assets",
        )

    error_messages = []

    for field_errors in form.errors.values():
        for error in field_errors:
            error_messages.append(str(error))

    messages.error(
        request,
        "تعذر إضافة الأصل: "
        + "، ".join(error_messages),
    )

    return redirect(
        "municipal_portal:services_assets",
    )


@municipal_required
@require_POST
def asset_import(request):
    form = AssetExcelUploadForm(
        request.POST,
        request.FILES,
    )

    if not form.is_valid():
        messages.error(
            request,
            "يرجى اختيار ملف Excel صحيح بصيغة xlsx.",
        )

        return redirect(
            "municipal_portal:services_assets",
        )

    excel_file = form.cleaned_data[
        "excel_file"
    ]

    try:
        workbook = load_workbook(
            excel_file,
            data_only=True,
        )

        worksheet = workbook.active

    except Exception:
        messages.error(
            request,
            "تعذر قراءة ملف Excel.",
        )

        return redirect(
            "municipal_portal:services_assets",
        )

    expected_headers = [
        "asset_code",
        "service",
        "asset_type",
        "name_ar",
        "neighborhood",
        "address",
        "latitude",
        "longitude",
        "status",
        "condition",
        "installation_date",
        "notes",
    ]

    received_headers = [
        str(cell.value).strip()
        if cell.value is not None
        else ""
        for cell in worksheet[1]
    ]

    if received_headers != expected_headers:
        messages.error(
            request,
            (
                "أعمدة ملف Excel غير صحيحة. "
                "استخدمي النموذج الذي يتم تنزيله من النظام."
            ),
        )

        return redirect(
            "municipal_portal:services_assets",
        )

    status_values = {
        value
        for value, label
        in MunicipalAsset.Status.choices
    }

    condition_values = {
        value
        for value, label
        in MunicipalAsset.Condition.choices
    }

    assets_to_create = []
    errors = []
    codes_in_file = set()

    for row_number, row in enumerate(
        worksheet.iter_rows(
            min_row=2,
            values_only=True,
        ),
        start=2,
    ):
        if not any(
            value not in (None, "")
            for value in row
        ):
            continue

        (
            asset_code,
            service_name,
            asset_type_name,
            name_ar,
            neighborhood_name,
            address,
            latitude,
            longitude,
            status,
            condition,
            installation_date,
            notes,
        ) = row

        asset_code = str(
            asset_code or ""
        ).strip()

        service_name = str(
            service_name or ""
        ).strip()

        asset_type_name = str(
            asset_type_name or ""
        ).strip()

        status = str(
            status or "operational"
        ).strip()

        condition = str(
            condition or "good"
        ).strip()

        if not asset_code:
            errors.append(
                f"الصف {row_number}: رمز الأصل مطلوب."
            )
            continue

        if asset_code in codes_in_file:
            errors.append(
                (
                    f"الصف {row_number}: رمز الأصل "
                    f"{asset_code} مكرر داخل الملف."
                )
            )
            continue

        if MunicipalAsset.objects.filter(
            asset_code=asset_code,
        ).exists():
            errors.append(
                (
                    f"الصف {row_number}: الأصل "
                    f"{asset_code} موجود مسبقًا."
                )
            )
            continue

        codes_in_file.add(asset_code)

        try:
            service = MunicipalService.objects.get(
                name_ar__iexact=service_name,
            )
        except MunicipalService.DoesNotExist:
            errors.append(
                (
                    f"الصف {row_number}: الخدمة "
                    f"{service_name} غير موجودة."
                )
            )
            continue

        try:
            asset_type = AssetType.objects.get(
                service=service,
                name_ar__iexact=asset_type_name,
            )
        except AssetType.DoesNotExist:
            errors.append(
                (
                    f"الصف {row_number}: نوع الأصل "
                    f"{asset_type_name} غير موجود "
                    f"ضمن خدمة {service.name_ar}."
                )
            )
            continue

        neighborhood = None

        if neighborhood_name:
            neighborhood = Neighborhood.objects.filter(
                name_ar__iexact=str(
                    neighborhood_name
                ).strip(),
            ).first()

            if neighborhood is None:
                errors.append(
                    (
                        f"الصف {row_number}: الحي "
                        f"{neighborhood_name} غير موجود."
                    )
                )
                continue

        try:
            latitude_value = float(latitude)
            longitude_value = float(longitude)

            if not -90 <= latitude_value <= 90:
                raise ValueError

            if not -180 <= longitude_value <= 180:
                raise ValueError

        except (TypeError, ValueError):
            errors.append(
                (
                    f"الصف {row_number}: "
                    "الإحداثيات غير صحيحة."
                )
            )
            continue

        if status not in status_values:
            errors.append(
                (
                    f"الصف {row_number}: "
                    f"حالة التشغيل {status} غير صحيحة."
                )
            )
            continue

        if condition not in condition_values:
            errors.append(
                (
                    f"الصف {row_number}: "
                    f"الحالة الفنية {condition} غير صحيحة."
                )
            )
            continue

        parsed_installation_date = None

        if installation_date:
            try:
                if isinstance(
                    installation_date,
                    datetime,
                ):
                    parsed_installation_date = (
                        installation_date.date()
                    )

                elif isinstance(
                    installation_date,
                    date,
                ):
                    parsed_installation_date = (
                        installation_date
                    )

                else:
                    parsed_installation_date = (
                        date.fromisoformat(
                            str(
                                installation_date
                            ).strip()
                        )
                    )

            except ValueError:
                errors.append(
                    (
                        f"الصف {row_number}: "
                        "تاريخ التركيب غير صحيح. "
                        "استخدمي YYYY-MM-DD."
                    )
                )
                continue

        asset = MunicipalAsset(
            asset_code=asset_code,
            asset_type=asset_type,
            name_ar=str(
                name_ar or ""
            ).strip(),
            neighborhood=neighborhood,
            address=str(
                address or ""
            ).strip(),
            location=Point(
                longitude_value,
                latitude_value,
                srid=4326,
            ),
            status=status,
            condition=condition,
            installation_date=(
                parsed_installation_date
            ),
            notes=str(
                notes or ""
            ).strip(),
        )

        assets_to_create.append(asset)

    if errors:
        for error in errors[:10]:
            messages.error(
                request,
                error,
            )

        if len(errors) > 10:
            messages.error(
                request,
                (
                    f"يوجد {len(errors) - 10} "
                    "أخطاء إضافية في الملف."
                ),
            )

        return redirect(
            "municipal_portal:services_assets",
        )

    if not assets_to_create:
        messages.warning(
            request,
            "لا توجد صفوف صالحة للاستيراد.",
        )

        return redirect(
            "municipal_portal:services_assets",
        )

    with transaction.atomic():
        MunicipalAsset.objects.bulk_create(
            assets_to_create,
        )

    messages.success(
        request,
        (
            f"تم استيراد {len(assets_to_create)} "
            "أصل بنجاح."
        ),
    )

    return redirect(
        "municipal_portal:services_assets",
    )


@municipal_required
def asset_excel_template(request):
    workbook = Workbook()

    worksheet = workbook.active
    worksheet.title = "الأصول البلدية"

    headers = [
        "asset_code",
        "service",
        "asset_type",
        "name_ar",
        "neighborhood",
        "address",
        "latitude",
        "longitude",
        "status",
        "condition",
        "installation_date",
        "notes",
    ]

    worksheet.append(headers)

    worksheet.append(
        [
            "LIGHT-001",
            "الإنارة العامة",
            "عمود إنارة",
            "عمود إنارة شارع الزبيري",
            "",
            "شارع الزبيري",
            15.3694000,
            44.1910000,
            "operational",
            "good",
            "2026-01-15",
            "",
        ]
    )

    widths = {
        "A": 18,
        "B": 24,
        "C": 22,
        "D": 32,
        "E": 22,
        "F": 34,
        "G": 18,
        "H": 18,
        "I": 24,
        "J": 18,
        "K": 22,
        "L": 35,
    }

    for column, width in widths.items():
        worksheet.column_dimensions[
            column
        ].width = width

    output = BytesIO()
    workbook.save(output)
    output.seek(0)

    response = HttpResponse(
        output.getvalue(),
        content_type=(
            "application/vnd.openxmlformats-"
            "officedocument.spreadsheetml.sheet"
        ),
    )

    response[
        "Content-Disposition"
    ] = (
        'attachment; '
        'filename="cityvoice_assets_template.xlsx"'
    )

    return response

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
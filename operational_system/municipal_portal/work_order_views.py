from django.contrib import messages
from django.db import transaction
from django.shortcuts import (
    get_object_or_404,
    redirect,
)
from django.urls import reverse
from django.utils.http import (
    url_has_allowed_host_and_scheme,
)
from django.views.decorators.http import require_POST

from maintenance.models import (
    WorkOrder,
    WorkOrderAssignmentHistory,
)

from .complaint_forms import (
    WorkOrderReassignmentForm,
)
from .decorators import municipal_required


@municipal_required
@require_POST
@transaction.atomic
def reassign_work_order(request, work_order_id):
    work_order = get_object_or_404(
        WorkOrder.objects
        .select_for_update()
        .select_related(
            "complaint",
            "assigned_to",
        ),
        pk=work_order_id,
    )

    redirect_url = reverse(
        "municipal_portal:work_order_list"
    )

    requested_next = request.POST.get(
        "next",
        "",
    )

    if url_has_allowed_host_and_scheme(
        url=requested_next,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        redirect_url = requested_next

    if work_order.status != WorkOrder.Status.ASSIGNED:
        messages.error(
            request,
            (
                "يمكن إعادة الإسناد فقط قبل أن يقبل "
                "قائد الفريق المهمة."
            ),
        )

        return redirect(redirect_url)

    form = WorkOrderReassignmentForm(
        request.POST,
        current_worker=work_order.assigned_to,
    )

    if not form.is_valid():
        error_text = " ".join(
            error
            for errors in form.errors.values()
            for error in errors
        )

        messages.error(
            request,
            error_text or "تعذر إعادة إسناد أمر العمل.",
        )

        return redirect(redirect_url)

    previous_worker = work_order.assigned_to
    new_worker = form.cleaned_data["assigned_to"]
    reason = form.cleaned_data["reason"]

    if previous_worker.pk == new_worker.pk:
        messages.error(
            request,
            "اختر قائد فريق مختلفًا عن القائد الحالي.",
        )

        return redirect(redirect_url)

    WorkOrderAssignmentHistory.objects.create(
        work_order=work_order,
        previous_assigned_to=previous_worker,
        new_assigned_to=new_worker,
        reassigned_by=request.user,
        reason=reason,
    )

    work_order.assigned_to = new_worker
    work_order.save(
        update_fields=[
            "assigned_to",
            "updated_at",
        ]
    )

    messages.success(
        request,
        (
            "تمت إعادة إسناد أمر العمل "
            f"WO-{work_order.pk:06d} إلى "
            f"{new_worker.get_full_name().strip() or new_worker.username}."
        ),
    )

    return redirect(redirect_url)
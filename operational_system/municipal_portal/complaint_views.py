from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from complaints.models import Complaint, ComplaintHistory
from maintenance.models import MaintenanceTeam, WorkOrder

from .complaint_forms import (
    ComplaintAssignmentForm,
    ComplaintReviewForm,
)
from .decorators import municipal_required


def get_work_order(complaint):
    return (
        WorkOrder.objects
        .select_related(
            "team",
            "team__leader",
            "assigned_to",
            "assigned_by",
            "accepted_by",
        )
        .filter(complaint=complaint)
        .first()
    )


def add_validation_errors(form, error):
    if hasattr(error, "message_dict"):
        for field_name, field_errors in error.message_dict.items():
            target = (
                field_name
                if field_name in form.fields
                else None
            )

            for message in field_errors:
                form.add_error(target, message)
    else:
        for message in error.messages:
            form.add_error(None, message)


def complaint_snapshot(complaint):
    """نسخة من بيانات البلاغ قبل التعديل أو بعده."""

    return {
        "service": {
            "label": "الخدمة",
            "value": complaint.service_id,
            "display": str(complaint.service),
        },
        "category": {
            "label": "التصنيف",
            "value": complaint.category_id,
            "display": str(complaint.category),
        },
        "asset": {
            "label": "الأصل المرتبط",
            "value": complaint.asset_id,
            "display": (
                str(complaint.asset)
                if complaint.asset_id
                else "لا يوجد أصل مرتبط"
            ),
        },
        "priority": {
            "label": "الأولوية",
            "value": complaint.priority,
            "display": complaint.get_priority_display(),
        },
        "status": {
            "label": "الحالة",
            "value": complaint.status,
            "display": complaint.get_status_display(),
        },
    }


def get_changes(before, after):
    """تسجيل الحقول التي تغيرت فقط."""

    changes = {}

    for field_name, old_data in before.items():
        new_data = after[field_name]

        if old_data["value"] != new_data["value"]:
            changes[field_name] = {
                "label": old_data["label"],
                "old_value": old_data["value"],
                "new_value": new_data["value"],
                "old": old_data["display"],
                "new": new_data["display"],
            }

    return changes


def user_label(user):
    full_name = user.get_full_name().strip()
    username = user.get_username()

    if full_name:
        return f"{full_name} — {username}"

    return username


def assign_team_to_complaint(request, complaint, form):
    """
    استدعاء هذه الدالة داخل transaction.atomic،
    وبعد قفل البلاغ والتحقق من صحة النموذج.
    """

    selected_team = form.cleaned_data["team"]

    # قفل الفريق دون ضم جداول أخرى إلى استعلام القفل.
    team = (
        MaintenanceTeam.objects
        .select_for_update()
        .filter(pk=selected_team.pk)
        .first()
    )

    if team is None:
        form.add_error(
            "team",
            "الفريق المحدد لم يعد موجودًا.",
        )
        return False

    if not team.is_active:
        form.add_error(
            "team",
            "الفريق المحدد لم يعد نشطًا.",
        )
        return False

    if team.service_id != complaint.service_id:
        form.add_error(
            "team",
            "الفريق المحدد غير مختص بخدمة البلاغ.",
        )
        return False

    if not team.service.is_active:
        form.add_error(
            "team",
            "الخدمة التابعة للفريق غير نشطة.",
        )
        return False

    User = get_user_model()

    # قفل الحسابات بترتيب ثابت أثناء إصدار أمر العمل.
    locked_users = {
        user.pk: user
        for user in (
            User.objects
            .select_for_update()
            .filter(
                pk__in=[
                    team.leader_id,
                    request.user.pk,
                ]
            )
            .order_by("pk")
        )
    }

    leader = locked_users.get(team.leader_id)
    issuer = locked_users.get(request.user.pk)

    if (
        leader is None
        or not leader.is_active
        or leader.role != User.Role.FIELD_WORKER
    ):
        form.add_error(
            "team",
            "قائد الفريق لا يملك حساب صيانة نشطًا.",
        )
        return False

    if (
        issuer is None
        or not issuer.is_active
        or issuer.role not in {
            User.Role.MUNICIPAL_EMPLOYEE,
            User.Role.MUNICIPAL_MANAGER,
        }
    ):
        form.add_error(
            None,
            "إصدار أمر العمل يتطلب حسابًا نشطًا "
            "بدور موظف البلدية أو مدير البلدية.",
        )
        return False

    work_order = form.save(commit=False)

    work_order.complaint = complaint
    work_order.team = team
    work_order.assigned_to = leader
    work_order.assigned_by = issuer
    work_order.status = WorkOrder.Status.ASSIGNED
    work_order.scheduled_for = None

    try:
        work_order.full_clean()
    except ValidationError as error:
        add_validation_errors(form, error)
        return False

    before = complaint_snapshot(complaint)

    work_order.save()

    complaint.status = Complaint.Status.ASSIGNED
    complaint.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    after = complaint_snapshot(complaint)
    changes = get_changes(before, after)

    leader_name = user_label(leader)

    changes["team"] = {
        "label": "فريق الصيانة",
        "old_value": None,
        "new_value": team.pk,
        "old": "لم يُحدد فريق",
        "new": team.name,
    }

    changes["assigned_to"] = {
        "label": "قائد الفريق وقت الإسناد",
        "old_value": None,
        "new_value": leader.pk,
        "old": "لم يُسند",
        "new": leader_name,
    }

    changes["work_order"] = {
        "label": "رقم أمر العمل",
        "old_value": None,
        "new_value": work_order.pk,
        "old": "لا يوجد",
        "new": str(work_order.pk),
    }

    if work_order.instructions:
        changes["instructions"] = {
            "label": "تعليمات التنفيذ",
            "old_value": "",
            "new_value": work_order.instructions,
            "old": "لا توجد",
            "new": work_order.instructions,
        }

    ComplaintHistory.objects.create(
        complaint=complaint,
        actor=issuer,
        action=ComplaintHistory.Action.ASSIGNED,
        notes=(
            f"تم إنشاء أمر العمل وإسناده إلى فريق "
            f"«{team.name}»، بقيادة {leader_name}."
        ),
        changes=changes,
    )

    messages.success(
        request,
        f"تم إسناد البلاغ إلى فريق «{team.name}» "
        "وإنشاء أمر العمل وتسجيل الإجراء.",
    )

    return True


@municipal_required
@require_http_methods(["GET", "POST"])
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

    review_form = ComplaintReviewForm(
        instance=complaint,
        prefix="review",
    )

    assignment_form = ComplaintAssignmentForm(
        complaint=complaint,
        prefix="assignment",
    )

    if request.method == "POST":
        action = request.POST.get("action", "")

        if action == "review":
            with transaction.atomic():
                locked_complaint = (
                    Complaint.objects
                    .select_for_update()
                    .get(pk=complaint.pk)
                )

                # أخذ النسخة قبل فحص ModelForm.
                before = complaint_snapshot(
                    locked_complaint
                )

                was_submitted = (
                    locked_complaint.status
                    == Complaint.Status.SUBMITTED
                )

                review_form = ComplaintReviewForm(
                    request.POST,
                    instance=locked_complaint,
                    prefix="review",
                )

                if locked_complaint.status not in {
                    Complaint.Status.SUBMITTED,
                    Complaint.Status.UNDER_REVIEW,
                }:
                    review_form.add_error(
                        None,
                        "لا يمكن تعديل المراجعة بعد إسناد البلاغ "
                        "أو انتهاء معالجته.",
                    )

                elif WorkOrder.objects.filter(
                    complaint=locked_complaint
                ).exists():
                    review_form.add_error(
                        None,
                        "يوجد أمر عمل لهذا البلاغ بالفعل.",
                    )

                elif review_form.is_valid():
                    reviewed_complaint = review_form.save(
                        commit=False
                    )

                    reviewed_complaint.status = (
                        Complaint.Status.UNDER_REVIEW
                    )

                    after = complaint_snapshot(
                        reviewed_complaint
                    )

                    changes = get_changes(before, after)

                    if changes:
                        reviewed_complaint.save(
                            update_fields=[
                                "service",
                                "category",
                                "asset",
                                "priority",
                                "status",
                                "updated_at",
                            ]
                        )

                        ComplaintHistory.objects.create(
                            complaint=reviewed_complaint,
                            actor=request.user,
                            action=(
                                ComplaintHistory.Action.REVIEWED
                                if was_submitted
                                else ComplaintHistory.Action.UPDATED
                            ),
                            notes=(
                                "تم اعتماد مراجعة البلاغ."
                                if was_submitted
                                else "تم تعديل بيانات مراجعة البلاغ."
                            ),
                            changes=changes,
                        )

                        messages.success(
                            request,
                            "تم حفظ المراجعة وتسجيل الإجراء.",
                        )

                    else:
                        messages.info(
                            request,
                            "لم تتغير بيانات المراجعة.",
                        )

                    return redirect(
                        "municipal_portal:complaint_detail",
                        reference_number=reference_number,
                    )

        elif action == "assign":
            with transaction.atomic():
                locked_complaint = (
                    Complaint.objects
                    .select_for_update()
                    .get(pk=complaint.pk)
                )

                assignment_form = ComplaintAssignmentForm(
                    request.POST,
                    complaint=locked_complaint,
                    prefix="assignment",
                )

                if locked_complaint.status != (
                    Complaint.Status.UNDER_REVIEW
                ):
                    assignment_form.add_error(
                        None,
                        "يجب حفظ مراجعة البلاغ أولًا، "
                        "ولا يُسمح بالإسناد من حالته الحالية.",
                    )

                elif WorkOrder.objects.filter(
                    complaint=locked_complaint
                ).exists():
                    assignment_form.add_error(
                        None,
                        "يوجد أمر عمل لهذا البلاغ بالفعل. "
                        "لم يتم إنشاء أمر آخر.",
                    )

                elif assignment_form.is_valid():
                    assigned = assign_team_to_complaint(
                        request,
                        locked_complaint,
                        assignment_form,
                    )

                    if assigned:
                        return redirect(
                            "municipal_portal:complaint_detail",
                            reference_number=reference_number,
                        )

        else:
            messages.error(
                request,
                "الإجراء المطلوب غير معروف.",
            )

            return redirect(
                "municipal_portal:complaint_detail",
                reference_number=reference_number,
            )

        complaint.refresh_from_db()

        # تحديث النموذج غير المرسل من البيانات الفعلية.
        if action == "assign":
            review_form = ComplaintReviewForm(
                instance=complaint,
                prefix="review",
            )
        else:
            assignment_form = ComplaintAssignmentForm(
                complaint=complaint,
                prefix="assignment",
            )

    work_order = get_work_order(complaint)

    can_review = (
        complaint.status in {
            Complaint.Status.SUBMITTED,
            Complaint.Status.UNDER_REVIEW,
        }
        and work_order is None
    )

    can_assign = (
        complaint.status == Complaint.Status.UNDER_REVIEW
        and work_order is None
    )

    has_available_teams = (
        assignment_form.fields["team"]
        .queryset.exists()
    )

    history_entries = (
        complaint.history
        .select_related("actor")
        .order_by("-created_at", "-pk")
    )

    return render(
        request,
        "municipal_portal/complaints/detail.html",
        {
            "complaint": complaint,
            "work_order": work_order,
            "review_form": review_form,
            "assignment_form": assignment_form,
            "can_review": can_review,
            "can_assign": can_assign,
            "has_available_teams": has_available_teams,
            "history_entries": history_entries,
            "maptiler_api_key": getattr(
                settings,
                "MAPTILER_API_KEY",
                "",
            ),
        },
    )
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from complaints.models import Complaint

from .forms import ComplaintFeedbackForm
from .models import ComplaintFeedback


@login_required
def feedback_list(request):
    eligible_complaints = Complaint.objects.filter(
        citizen=request.user,
        status__in=[
            Complaint.Status.RESOLVED,
            Complaint.Status.CLOSED,
        ],
    ).select_related(
        "service",
        "category",
        "neighborhood",
    )

    pending_complaints = eligible_complaints.filter(
        feedback__isnull=True,
    )

    completed_complaints = eligible_complaints.filter(
        feedback__isnull=False,
    ).select_related(
        "feedback",
    )

    return render(
        request,
        "citizen_portal/home.html",
        {
            "page": "feedback",
            "pending_complaints": pending_complaints,
            "completed_complaints": completed_complaints,
        },
    )


@login_required
def submit_feedback(request, reference_number):
    complaint = get_object_or_404(
        Complaint,
        reference_number=reference_number,
        citizen=request.user,
    )

    allowed_statuses = [
        Complaint.Status.RESOLVED,
        Complaint.Status.CLOSED,
    ]

    if complaint.status not in allowed_statuses:
        return render(
            request,
            "feedback/feedback_unavailable.html",
            {
                "complaint": complaint,
            },
        )

    existing_feedback = ComplaintFeedback.objects.filter(
        complaint=complaint,
    ).first()

    if existing_feedback:
        return redirect(
            "feedback:feedback_success",
            reference_number=complaint.reference_number,
        )

    if request.method == "POST":
        form = ComplaintFeedbackForm(request.POST)

        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.complaint = complaint
            feedback.save()

            return redirect(
                "feedback:feedback_success",
                reference_number=complaint.reference_number,
            )
    else:
        form = ComplaintFeedbackForm()

    return render(
        request,
        "feedback/submit_feedback.html",
        {
            "form": form,
            "complaint": complaint,
        },
    )


@login_required
def feedback_success(request, reference_number):
    feedback = get_object_or_404(
        ComplaintFeedback,
        complaint__reference_number=reference_number,
        complaint__citizen=request.user,
    )

    return render(
        request,
        "feedback/feedback_success.html",
        {
            "feedback": feedback,
            "complaint": feedback.complaint,
        },
    )
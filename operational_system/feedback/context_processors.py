from complaints.models import Complaint


def feedback_notifications(request):
    if not request.user.is_authenticated:
        return {
            "pending_feedback_count": 0,
        }

    pending_count = Complaint.objects.filter(
        citizen=request.user,
        status__in=[
            Complaint.Status.RESOLVED,
            Complaint.Status.CLOSED,
        ],
        feedback__isnull=True,
    ).count()

    return {
        "pending_feedback_count": pending_count,
    }
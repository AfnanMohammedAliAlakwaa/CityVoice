from django.contrib.auth import get_user_model
from django.urls import reverse

from .models import Notification


def notify_municipality_of_new_complaint(complaint):
    """إنشاء إشعار بالبلاغ الجديد لموظفي البلدية ومديريها."""

    User = get_user_model()

    recipients = User.objects.filter(
        is_active=True,
        role__in=[
            User.Role.MUNICIPAL_EMPLOYEE,
            User.Role.MUNICIPAL_MANAGER,
        ],
    ).values_list("pk", flat=True)

    complaint_link = reverse(
        "municipal_portal:complaint_detail",
        kwargs={
            "reference_number": complaint.reference_number,
        },
    )

    notifications = [
        Notification(
            recipient_id=recipient_id,
            title="بلاغ جديد",
            message=(
                f"ورد بلاغ جديد برقم "
                f"{complaint.reference_number} "
                f"بخصوص {complaint.service.name_ar}، "
                f"بتصنيف {complaint.category.name_ar}."
            ),
            link=complaint_link,
        )
        for recipient_id in recipients
    ]

    return Notification.objects.bulk_create(
        notifications,
        batch_size=500,
    )
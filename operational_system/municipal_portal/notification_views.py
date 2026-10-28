from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from notifications.models import Notification

from .decorators import municipal_required


@never_cache
@municipal_required
@require_GET
def notification_summary(request):
    """إرجاع إشعارات المستخدم الحالي فقط دون تغيير قراءتها."""

    with transaction.atomic():
        notifications = Notification.objects.filter(
            recipient=request.user,
        )

        # تحديد آخر إشعار أولًا حتى تلتقط الدورة التالية
        # أي إشعارات تصل أثناء تجهيز هذه الاستجابة.
        latest_id = (
            notifications
            .order_by("-pk")
            .values_list("pk", flat=True)
            .first()
        )

        if latest_id is None:
            return JsonResponse(
                {
                    "unread_count": 0,
                    "latest_id": 0,
                    "latest_notification": None,
                }
            )

        current_notifications = notifications.filter(
            pk__lte=latest_id,
        )

        unread_count = current_notifications.filter(
            is_read=False,
        ).count()

        latest_notification = (
            current_notifications
            .filter(pk=latest_id)
            .values(
                "id",
                "title",
                "message",
                "created_at",
                "is_read",
            )
            .first()
        )

    return JsonResponse(
        {
            "unread_count": unread_count,
            "latest_id": latest_id,
            "latest_notification": latest_notification,
        }
    )
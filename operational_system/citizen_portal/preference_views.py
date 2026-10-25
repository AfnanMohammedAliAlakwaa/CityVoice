from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST


@require_POST
@login_required
def save_theme(request):
    theme = request.POST.get("theme")

    if theme not in {"light", "dark"}:
        return JsonResponse(
            {"ok": False, "message": "المظهر غير صالح."},
            status=400,
        )

    request.user.preferred_theme = theme
    request.user.save(update_fields=["preferred_theme"])

    return JsonResponse(
        {
            "ok": True,
            "theme": theme,
        }
    )
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from .forms import AvatarForm


@login_required
@require_POST
def update_avatar(request):
    user = request.user
    action = request.POST.get("action", "upload")

    if action == "delete":
        if user.avatar:
            user.avatar.delete(save=False)
            user.avatar = ""
            user.save(update_fields=["avatar"])

            messages.success(
                request,
                "تم حذف الصورة الشخصية.",
            )
        else:
            messages.info(
                request,
                "لا توجد صورة شخصية لحذفها.",
            )

        return redirect(
            request.POST.get(
                "next",
                "municipal_portal:dashboard",
            )
        )

    old_avatar_name = (
        user.avatar.name
        if user.avatar
        else ""
    )

    form = AvatarForm(
        request.POST,
        request.FILES,
        instance=user,
    )

    if form.is_valid():
        updated_user = form.save()

        new_avatar_name = (
            updated_user.avatar.name
            if updated_user.avatar
            else ""
        )

        if (
            old_avatar_name
            and old_avatar_name != new_avatar_name
        ):
            updated_user.avatar.storage.delete(
                old_avatar_name
            )

        messages.success(
            request,
            "تم تحديث الصورة الشخصية بنجاح.",
        )
    else:
        error_text = " ".join(
            error
            for errors in form.errors.values()
            for error in errors
        )

        messages.error(
            request,
            error_text or "تعذر تحديث الصورة الشخصية.",
        )

    return redirect(
        request.POST.get(
            "next",
            "municipal_portal:dashboard",
        )
    )
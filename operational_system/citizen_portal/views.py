from django.contrib.auth import (
    get_user_model,
    login as auth_login,
    logout as auth_logout,
)
from django.contrib.auth.decorators import login_required
from django.core import signing
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_POST
from django.conf import settings
from accounts.models import EmailVerification
from complaints.models import Complaint
from municipal_services.models import ServiceCategory

from .account_forms import (
    CitizenAccountForm,
    CitizenLoginForm,
    CitizenRegistrationForm,
)
from .forms import CitizenComplaintForm


LAST_USER_COOKIE = "cityvoice_last_username"
LAST_USER_SALT = "citizen_portal.last_username"
LAST_USER_MAX_AGE = 60 * 60 * 24 * 365


def remember_username(request, response, username):
    # المعلومة المحفوظة اسم المستخدم فقط.
    # هذا الملف لا يمنح صلاحية الدخول إلى الحساب.
    value = signing.dumps(
        username,
        salt=LAST_USER_SALT,
    )

    response.set_cookie(
        LAST_USER_COOKIE,
        value,
        max_age=LAST_USER_MAX_AGE,
        httponly=True,
        secure=request.is_secure(),
        samesite="Lax",
        path="/",
    )

    return response


def get_remembered_username(request):
    value = request.COOKIES.get(LAST_USER_COOKIE)

    if not value:
        return ""

    try:
        username = signing.loads(
            value,
            salt=LAST_USER_SALT,
            max_age=LAST_USER_MAX_AGE,
        )
    except (signing.BadSignature, ValueError, TypeError):
        return ""

    if not isinstance(username, str):
        return ""

    User = get_user_model()

    # لا نعرض حسابًا محذوفًا أو معطّلًا.
    user = User.objects.filter(
        username=username,
        is_active=True,
        role=User.Role.CITIZEN,
    ).first()

    return user.get_username() if user else ""


def get_safe_next_url(request):
    next_url = (
        request.POST.get("next")
        or request.GET.get("next")
    )

    if next_url and url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url

    return None


def show_account_choice(request, username, next_url):
    response = render(
        request,
        "citizen_portal/account_choice.html",
        {
            "remembered_username": username,
            "next_url": next_url or "",
        },
    )

    return remember_username(
        request,
        response,
        username,
    )


def complete_citizen_login(request, user, next_url):
    auth_login(request, user)

    if not user.has_verified_contact:
        response = redirect(
            "citizen_portal:verify_contact"
        )
    else:
        response = redirect(
            next_url or "citizen_portal:home"
        )

    return remember_username(
        request,
        response,
        user.get_username(),
    )


@never_cache
@require_http_methods(["GET", "POST"])
def citizen_auth(request):
    next_url = get_safe_next_url(request)

    if request.user.is_authenticated:
        remembered_username = request.user.get_username()
    else:
        remembered_username = get_remembered_username(request)

    choice = (
        request.POST.get("account_choice")
        if request.method == "POST"
        else None
    )

    explicit_mode = (
        request.GET.get("mode")
        if request.method == "GET"
        else None
    )

    if choice in {"login", "register"}:
        # اختيار أحد الزرين يفتح النموذج فقط.
        # حتى الحساب السابق يحتاج إدخال كلمة مروره.
        if request.user.is_authenticated:
            auth_logout(request)

        action = choice
        process_credentials = False

    elif request.user.is_authenticated:
        return show_account_choice(
            request,
            remembered_username,
            next_url,
        )

    elif request.method == "GET":
        if explicit_mode in {"login", "register"}:
            action = explicit_mode

        elif remembered_username:
            return show_account_choice(
                request,
                remembered_username,
                next_url,
            )

        else:
            action = "login"

        process_credentials = False

    else:
        action = request.POST.get("action", "login")
        process_credentials = True

    if action not in {"login", "register"}:
        action = "login"

    login_form = CitizenLoginForm(
        request=request,
        prefix="login",
        initial={
            "username": (
                remembered_username
                if action == "login"
                else ""
            ),
        },
    )

    registration_form = CitizenRegistrationForm(
        prefix="register",
    )

    if process_credentials:
        if action == "register":
            registration_form = CitizenRegistrationForm(
                request.POST,
                prefix="register",
            )

            if registration_form.is_valid():
                user = registration_form.save()

                return complete_citizen_login(
                    request,
                    user,
                    next_url,
                )

        else:
            login_form = CitizenLoginForm(
                request=request,
                data=request.POST,
                prefix="login",
            )

            if login_form.is_valid():
                user = login_form.get_user()

                if user.role != user.Role.CITIZEN:
                    login_form.add_error(
                        None,
                        "هذا الحساب غير مخصص لتطبيق المواطن.",
                    )

                else:
                    return complete_citizen_login(
                        request,
                        user,
                        next_url,
                    )

    response = render(
        request,
        "citizen_portal/auth.html",
        {
            "login_form": login_form,
            "registration_form": registration_form,
            "auth_mode": action,
            "next_url": next_url or "",
            "next": next_url or "",
        },
    )

    if remembered_username:
        return remember_username(
            request,
            response,
            remembered_username,
        )

    return response


@never_cache
@login_required
@require_POST
def citizen_logout(request):
    # نحصل على الاسم قبل إنهاء الجلسة.
    username = request.user.get_username()

    auth_logout(request)

    response = redirect("citizen_portal:auth")

    # يبقى الاسم فقط لعرض شاشة اختيار الحساب.
    return remember_username(
        request,
        response,
        username,
    )


def citizen_complaints(user):
    return (
        Complaint.objects.filter(citizen=user)
        .select_related(
            "service",
            "category",
            "neighborhood",
        )
        .order_by("-created_at", "-pk")
    )


@login_required
def home(request):
    complaints = citizen_complaints(request.user)

    active_statuses = [
        Complaint.Status.SUBMITTED,
        Complaint.Status.UNDER_REVIEW,
        Complaint.Status.ASSIGNED,
        Complaint.Status.IN_PROGRESS,
    ]

    return render(
        request,
        "citizen_portal/home.html",
        {
            "page": "home",
            "recent_complaints": complaints[:3],
            "active_count": complaints.filter(
                status__in=active_statuses
            ).count(),
            "latest_complaint": complaints.first(),
        },
    )


@login_required
def complaint_list(request):
    return render(
        request,
        "citizen_portal/home.html",
        {
            "page": "complaints",
            "complaints": citizen_complaints(request.user),
        },
    )


@login_required
def complaint_detail(request, reference_number):
    complaint = get_object_or_404(
        citizen_complaints(request.user),
        reference_number=reference_number,
    )

    return render(
        request,
        "citizen_portal/home.html",
        {
            "page": "detail",
            "complaint": complaint,
        },
    )


@login_required
def account(request):
    User = get_user_model()

    if request.method == "POST":
        with transaction.atomic():
            user = (
                User.objects.select_for_update()
                .get(pk=request.user.pk)
            )

            original_email = user.email or ""
            original_verified_contact = user.has_verified_contact

            form = CitizenAccountForm(
                request.POST,
                request.FILES,
                instance=user,
            )

            if form.is_valid():
                candidate_email = (
                    form.cleaned_data.get("email") or ""
                ).strip().lower()

                profile = form.save(commit=False)

                # يبقى البريد القديم حتى تأكيد الجديد.
                profile.email = original_email

                needs_verification = bool(candidate_email) and (
                    candidate_email != original_email.strip().lower()
                    or not original_verified_contact
                )

                profile.pending_email = (
                    candidate_email
                    if needs_verification
                    else ""
                )

                profile.save()

                EmailVerification.objects.filter(
                    user=user
                ).exclude(
                    target=profile.pending_email
                ).update(
                    code_hash=""
                )

                if needs_verification:
                    return redirect(
                        "citizen_portal:verify_contact"
                    )

                return redirect(
                    "citizen_portal:account_saved"
                )

    else:
        form = CitizenAccountForm(
            instance=request.user
        )

    return render(
        request,
        "citizen_portal/account.html",
        {
            "page": "account",
            "form": form,
            "saved": False,
        },
    )


@login_required
def account_saved(request):
    return render(
        request,
        "citizen_portal/account.html",
        {
            "page": "account",
            "form": CitizenAccountForm(
                instance=request.user
            ),
            "saved": True,
        },
    )


@login_required
def submit_complaint(request):
    if request.method == "POST":
        uploaded_files = request.FILES.copy()
        camera_photo = uploaded_files.get("camera_photo")

        if camera_photo:
            uploaded_files["photo"] = camera_photo

        form = CitizenComplaintForm(
            request.POST,
            uploaded_files,
        )

        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.citizen = request.user
            complaint.save()

            return redirect(
                "citizen_portal:complaint_success",
                reference_number=complaint.reference_number,
            )

    else:
        form = CitizenComplaintForm()

    return render(
        request,
        "citizen_portal/submit_complaint.html",
        {
            "form": form,
            "maptiler_api_key": settings.MAPTILER_API_KEY,
        },
    )

@login_required
def complaint_success(request, reference_number):
    complaint = get_object_or_404(
        Complaint,
        reference_number=reference_number,
        citizen=request.user,
    )

    return render(
        request,
        "citizen_portal/complaint_success.html",
        {"complaint": complaint},
    )


@login_required
@login_required
def load_categories(request):
    service_id = request.GET.get("service")

    categories = ServiceCategory.objects.filter(
        service_id=service_id
    ).order_by("name_ar")

    data = list(
        categories.values(
            "id",
            "name_ar",
        )
    )

    # وضع خيار "أخرى" في نهاية القائمة دائمًا
    data.sort(
        key=lambda category: (
            category["name_ar"].strip() in {"أخرى", "اخرى"},
            category["name_ar"],
        )
    )

    return JsonResponse(data, safe=False)
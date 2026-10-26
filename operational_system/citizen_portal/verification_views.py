import secrets
from datetime import timedelta
from smtplib import SMTPException

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import (
    check_password,
    make_password,
)
from django.core.exceptions import ImproperlyConfigured
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from accounts.models import EmailVerification


class EmailTargetForm(forms.Form):
    email = forms.EmailField(
        label="البريد الإلكتروني",
        max_length=254,
        widget=forms.EmailInput(
            attrs={
                "dir": "ltr",
                "autocomplete": "email",
            }
        ),
    )

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()


class CodeForm(forms.Form):
    code = forms.RegexField(
        regex=r"^[0-9]{6}$",
        label="رمز التحقق",
        min_length=6,
        max_length=6,
        error_messages={
            "invalid": "أدخل رمزًا من ستة أرقام.",
        },
        widget=forms.TextInput(
            attrs={
                "inputmode": "numeric",
                "autocomplete": "one-time-code",
                "dir": "ltr",
            }
        ),
    )


def email_in_use(user, target):
    User = get_user_model()

    other_users = User.objects.exclude(
        pk=user.pk
    )

    return (
        other_users.filter(
            email__iexact=target
        ).exists()
        or other_users.filter(
            verified_email__iexact=target
        ).exists()
    )


def send_code(user_id, target):
    User = get_user_model()
    now = timezone.now()

    with transaction.atomic():
        user = (
            User.objects.select_for_update()
            .get(pk=user_id)
        )

        challenge, _ = (
            EmailVerification.objects.get_or_create(
                user=user
            )
        )

        if (
            user.has_verified_contact
            and target == user.verified_email
        ):
            return False, "هذا البريد موثّق بالفعل."

        if email_in_use(user, target):
            return False, (
                "لا يمكن استخدام هذا البريد لهذا الحساب."
            )

        if (
            challenge.blocked_until
            and challenge.blocked_until > now
        ):
            return False, (
                "توقّف التحقق مؤقتًا بسبب المحاولات المتكررة. "
                "حاول بعد 15 دقيقة."
            )

        if (
            challenge.last_sent_at
            and now - challenge.last_sent_at
            < timedelta(seconds=60)
        ):
            return False, (
                "انتظر دقيقة بين طلبات إرسال الرمز."
            )

        if (
            not challenge.window_started_at
            or now - challenge.window_started_at
            >= timedelta(hours=1)
        ):
            challenge.window_started_at = now
            challenge.send_count = 0

        if challenge.send_count >= 5:
            return False, (
                "وصلت إلى الحد المسموح للإرسال. "
                "حاول لاحقًا بعد انتهاء الساعة."
            )

        if not getattr(
            settings,
            "CONTACT_EMAIL_ENABLED",
            False,
        ):
            return False, (
                "إرسال البريد غير مفعّل بعد. "
                "يلزم إعداد بريد المشروع أولًا."
            )

        backend = settings.EMAIL_BACKEND

        if (
            backend
            != "django.core.mail.backends.smtp.EmailBackend"
        ):
            test_backend_allowed = (
                settings.DEBUG
                and getattr(
                    settings,
                    "CONTACT_ALLOW_TEST_BACKEND",
                    False,
                )
            )

            if not test_backend_allowed:
                return False, (
                    "إعداد الإرسال غير صالح للتحقق الحقيقي."
                )

        code = (
            f"{secrets.randbelow(1000000):06d}"
        )

        challenge.target = target
        challenge.code_hash = make_password(code)
        challenge.expires_at = (
            now + timedelta(minutes=5)
        )
        challenge.attempts = 0
        challenge.blocked_until = None
        challenge.last_sent_at = now
        challenge.send_count += 1

        user.pending_email = target
        user.save(
            update_fields=["pending_email"]
        )

        try:
            delivered = send_mail(
                subject="CityVoice — رمز تأكيد البريد",
                message=(
                    f"رمز تأكيد بريدك في CityVoice: {code}\n"
                    "صالح لمدة 5 دقائق ويُستخدم مرة واحدة.\n"
                    "لا تشارك الرمز مع أي شخص.\n"
                    "إذا لم تطلبه فتجاهل الرسالة."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[target],
                fail_silently=False,
            )

            if delivered != 1:
                raise OSError(
                    "لم تقبل خدمة البريد الرسالة."
                )

        except (
            SMTPException,
            OSError,
            ValueError,
            ImproperlyConfigured,
        ):
            challenge.code_hash = ""
            challenge.save()

            return False, (
                "تعذر إرسال الرسالة. "
                "تحقق من إعدادات البريد أو حاول لاحقًا."
            )

        challenge.save()

        return True, (
            "تم إرسال الرمز. راجع صندوق الوارد "
            "والبريد غير المرغوب فيه."
        )


def confirm_code(user_id, code):
    User = get_user_model()
    now = timezone.now()

    try:
        with transaction.atomic():
            user = (
                User.objects.select_for_update()
                .get(pk=user_id)
            )

            challenge = (
                EmailVerification.objects.filter(
                    user=user
                ).first()
            )

            if not challenge or not challenge.code_hash:
                return False, (
                    "اطلب رمز تحقق جديدًا أولًا."
                )

            if (
                challenge.blocked_until
                and challenge.blocked_until > now
            ):
                return False, (
                    "توقّف التحقق مؤقتًا. "
                    "حاول بعد 15 دقيقة."
                )

            if (
                not challenge.expires_at
                or challenge.expires_at <= now
            ):
                challenge.code_hash = ""
                challenge.save(
                    update_fields=["code_hash"]
                )

                return False, (
                    "انتهت صلاحية الرمز. "
                    "اطلب رمزًا جديدًا."
                )

            if challenge.target != user.pending_email:
                challenge.code_hash = ""
                challenge.save(
                    update_fields=["code_hash"]
                )

                return False, (
                    "تغيّر البريد المطلوب. "
                    "اطلب رمزًا جديدًا."
                )

            if not check_password(
                code,
                challenge.code_hash,
            ):
                challenge.attempts += 1

                if challenge.attempts >= 5:
                    challenge.code_hash = ""
                    challenge.blocked_until = (
                        now + timedelta(minutes=15)
                    )

                challenge.save()

                return False, (
                    "الرمز غير صحيح أو تجاوزت "
                    "عدد المحاولات."
                )

            if email_in_use(
                user,
                challenge.target,
            ):
                challenge.code_hash = ""
                challenge.save(
                    update_fields=["code_hash"]
                )

                return False, (
                    "لا يمكن اعتماد هذا البريد. "
                    "استخدم بريدًا آخر."
                )

            user.email = challenge.target
            user.verified_email = challenge.target
            user.email_verified_at = now
            user.pending_email = ""

            user.save(
                update_fields=[
                    "email",
                    "verified_email",
                    "email_verified_at",
                    "pending_email",
                ]
            )

            # إلغاء الرمز بعد استخدامه بنجاح.
            challenge.code_hash = ""
            challenge.expires_at = None

            challenge.save(
                update_fields=[
                    "code_hash",
                    "expires_at",
                ]
            )

            return True, "تم تأكيد البريد بنجاح."

    except IntegrityError:
        return False, (
            "تعذر اعتماد البريد لأنه مرتبط بحساب آخر."
        )


@login_required
@never_cache
@require_http_methods(["GET", "POST"])
def verify_contact(request):
    target = (
        request.user.pending_email
        or request.user.email
    )

    email_form = EmailTargetForm(
        initial={"email": target}
    )

    code_form = CodeForm()
    error = ""

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "send":
            email_form = EmailTargetForm(
                request.POST
            )

            if email_form.is_valid():
                success, message = send_code(
                    request.user.pk,
                    email_form.cleaned_data["email"],
                )

                if success:
                    return redirect(
                        "citizen_portal:verify_contact_sent"
                    )

                error = message

        elif action == "confirm":
            code_form = CodeForm(
                request.POST
            )

            if code_form.is_valid():
                success, message = confirm_code(
                    request.user.pk,
                    code_form.cleaned_data["code"],
                )

                if success:
                    return redirect(
                        "citizen_portal:home"
                    )

                error = message

        else:
            error = "الطلب غير صالح."

    request.user.refresh_from_db()

    challenge = (
        EmailVerification.objects.filter(
            user=request.user
        ).first()
    )

    return render(
        request,
        "citizen_portal/verify_contact.html",
        {
            "page": "verification",
            "email_form": email_form,
            "code_form": code_form,
            "error": error,
            "sent": (
                request.resolver_match.url_name
                == "verify_contact_sent"
            ),
            "pending_target": (
                request.user.pending_email
            ),
            "has_challenge": bool(
                challenge
                and challenge.code_hash
            ),
        },
    )
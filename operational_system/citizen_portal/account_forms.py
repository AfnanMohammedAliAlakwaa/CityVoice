from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserCreationForm,
)


User = get_user_model()


class CitizenLoginForm(AuthenticationForm):
    """نموذج تسجيل الدخول الخاص بتطبيق المواطن."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["username"].label = "اسم المستخدم"
        self.fields["username"].widget.attrs.update(
            {
                "placeholder": " ",
                "autocomplete": "username",
                "autofocus": True,
            }
        )

        self.fields["password"].label = "كلمة المرور"
        self.fields["password"].widget.attrs.update(
            {
                "placeholder": " ",
                "autocomplete": "current-password",
            }
        )

        self.error_messages.update(
            {
                "invalid_login": (
                    "اسم المستخدم أو كلمة المرور غير صحيحة."
                ),
                "inactive": "هذا الحساب غير نشط.",
            }
        )


class CitizenRegistrationForm(UserCreationForm):
    """نموذج إنشاء حساب مواطن جديد."""

    email = forms.EmailField(
        label="البريد الإلكتروني",
        required=True,
        widget=forms.EmailInput(
            attrs={
                "placeholder": " ",
                "autocomplete": "email",
                "dir": "ltr",
            }
        ),
    )

    phone_number = forms.CharField(
        label="رقم الهاتف",
        required=False,
        max_length=20,
        widget=forms.TextInput(
            attrs={
                "placeholder": " ",
                "type": "tel",
                "autocomplete": "tel",
                "dir": "ltr",
            }
        ),
    )

    error_messages = {
        "password_mismatch": "كلمتا المرور غير متطابقتين.",
    }

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "username",
            "email",
            "phone_number",
            "password1",
            "password2",
        ]

        labels = {
            "first_name": "الاسم الأول",
            "last_name": "اسم العائلة",
            "username": "اسم المستخدم",
        }

        widgets = {
            "first_name": forms.TextInput(
                attrs={
                    "placeholder": " ",
                    "autocomplete": "given-name",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "placeholder": " ",
                    "autocomplete": "family-name",
                }
            ),
            "username": forms.TextInput(
                attrs={
                    "placeholder": " ",
                    "autocomplete": "username",
                    "dir": "ltr",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["first_name"].required = True
        self.fields["last_name"].required = True

        self.fields["username"].error_messages["unique"] = (
            "اسم المستخدم مستخدم مسبقًا."
        )

        self.fields["password1"].label = "كلمة المرور"
        self.fields["password1"].help_text = ""
        self.fields["password1"].widget.attrs.update(
            {
                "placeholder": " ",
                "autocomplete": "new-password",
            }
        )

        self.fields["password2"].label = "تأكيد كلمة المرور"
        self.fields["password2"].help_text = ""
        self.fields["password2"].widget.attrs.update(
            {
                "placeholder": " ",
                "autocomplete": "new-password",
            }
        )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "البريد الإلكتروني مستخدم مسبقًا."
            )

        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.CITIZEN
        user.email = self.cleaned_data["email"]
        user.phone_number = self.cleaned_data.get(
            "phone_number",
            "",
        )

        if commit:
            user.save()

        return user


class CitizenAccountForm(forms.ModelForm):
    """نموذج تعديل بيانات حساب المواطن."""

    class Meta:
        model = User

        fields = [
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "avatar",
            "neighborhood_name",
            "default_address",
            "preferred_theme",
        ]

        labels = {
            "first_name": "الاسم الأول",
            "last_name": "اسم العائلة",
            "email": "البريد الإلكتروني",
            "phone_number": "رقم الهاتف",
            "avatar": "الصورة الشخصية",
            "neighborhood_name": "الحي",
            "default_address": "العنوان",
            "preferred_theme": "المظهر",
        }

        widgets = {
            "first_name": forms.TextInput(
                attrs={"autocomplete": "given-name"}
            ),
            "last_name": forms.TextInput(
                attrs={"autocomplete": "family-name"}
            ),
            "email": forms.EmailInput(
                attrs={
                    "autocomplete": "email",
                    "dir": "ltr",
                }
            ),
            "phone_number": forms.TextInput(
                attrs={
                    "type": "tel",
                    "autocomplete": "tel",
                    "dir": "ltr",
                }
            ),
            "avatar": forms.ClearableFileInput(
                attrs={
                    "accept": "image/jpeg,image/png,image/webp",
                }
            ),
            "neighborhood_name": forms.TextInput(),
            "default_address": forms.Textarea(
                attrs={
                    "rows": 3,
                    "autocomplete": "street-address",
                }
            ),
            "preferred_theme": forms.RadioSelect(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name in [
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "avatar",
            "neighborhood_name",
            "default_address",
        ]:
            self.fields[name].required = False

    def clean_avatar(self):
        avatar = self.cleaned_data.get("avatar")

        if not avatar or "avatar" not in self.files:
            return avatar

        if avatar.size > 5 * 1024 * 1024:
            raise forms.ValidationError(
                "حجم الصورة يجب ألا يتجاوز 5 ميجابايت."
            )

        image_format = getattr(
            getattr(avatar, "image", None),
            "format",
            "",
        )

        if image_format not in {"JPEG", "PNG", "WEBP"}:
            raise forms.ValidationError(
                "اختاري صورة بصيغة JPG أو PNG أو WEBP."
            )

        return avatar
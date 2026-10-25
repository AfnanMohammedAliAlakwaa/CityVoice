from django import forms
from django.contrib.auth import get_user_model


User = get_user_model()


class CitizenAccountForm(forms.ModelForm):
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
from pathlib import Path

from django import forms

from .models import User


class AvatarForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["avatar"]

    def clean_avatar(self):
        avatar = self.cleaned_data.get("avatar")

        if not avatar:
            raise forms.ValidationError(
                "يرجى اختيار صورة شخصية."
            )

        maximum_size = 3 * 1024 * 1024

        if avatar.size > maximum_size:
            raise forms.ValidationError(
                "حجم الصورة يجب ألا يتجاوز 3 ميجابايت."
            )

        allowed_extensions = {
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
        }

        extension = Path(avatar.name).suffix.lower()

        if extension not in allowed_extensions:
            raise forms.ValidationError(
                "الصيغ المسموحة هي JPG وPNG وWEBP فقط."
            )

        allowed_content_types = {
            "image/jpeg",
            "image/png",
            "image/webp",
        }

        if (
            avatar.content_type
            and avatar.content_type not in allowed_content_types
        ):
            raise forms.ValidationError(
                "الملف المختار ليس صورة صالحة."
            )

        return avatar
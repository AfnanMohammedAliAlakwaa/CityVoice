from django import forms

from maintenance.models import WorkOrder


class WorkOrderCompletionForm(forms.ModelForm):
    class Meta:
        model = WorkOrder

        fields = [
            "completion_notes",
            "completion_photo",
        ]

        labels = {
            "completion_notes": "ملاحظات الإنجاز",
            "completion_photo": "صورة بعد الإنجاز",
        }

        widgets = {
            "completion_notes": forms.Textarea(
                attrs={
                    "class": "task-input",
                    "rows": 5,
                    "placeholder": (
                        "اشرح الأعمال التي نُفذت، "
                        "والنتيجة وأي ملاحظات مهمة."
                    ),
                }
            ),
            "completion_photo": forms.ClearableFileInput(
                attrs={
                    "class": "task-file-input",
                    "accept": "image/*",
                    "capture": "environment",
                }
            ),
        }

        error_messages = {
            "completion_notes": {
                "required": "أضف ملاحظات الإنجاز.",
            },
            "completion_photo": {
                "required": "أرفق صورة توضح نتيجة العمل.",
                "invalid_image": "الملف المحدد ليس صورة صالحة.",
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["completion_notes"].required = True
        self.fields["completion_photo"].required = True

    def clean_completion_notes(self):
        notes = (
            self.cleaned_data.get("completion_notes")
            or ""
        ).strip()

        if len(notes) < 10:
            raise forms.ValidationError(
                "اكتب ملاحظات أوضح عن العمل المنجز."
            )

        return notes

    def clean_completion_photo(self):
        photo = self.cleaned_data.get("completion_photo")

        if not photo:
            raise forms.ValidationError(
                "أرفق صورة توضح نتيجة العمل."
            )

        maximum_size = 5 * 1024 * 1024

        if photo.size > maximum_size:
            raise forms.ValidationError(
                "يجب ألا يتجاوز حجم الصورة 5 ميجابايت."
            )

        return photo
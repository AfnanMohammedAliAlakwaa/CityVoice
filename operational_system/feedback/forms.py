from django import forms

from .models import ComplaintFeedback


class ComplaintFeedbackForm(forms.ModelForm):
    class Meta:
        model = ComplaintFeedback
        fields = [
            "rating",
            "comment",
        ]

        widgets = {
            "rating": forms.HiddenInput(),
            "comment": forms.Textarea(
                attrs={
                    "class": "feedback-comment",
                    "placeholder": (
                        "أخبرنا عن تجربتك مع معالجة الشكوى "
                        "(اختياري)"
                    ),
                    "rows": 4,
                    "maxlength": 1000,
                }
            ),
        }

        labels = {
            "rating": "تقييم الخدمة",
            "comment": "هل لديك ملاحظات إضافية؟",
        }
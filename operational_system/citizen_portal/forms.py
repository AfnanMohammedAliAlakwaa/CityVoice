from django import forms
from django.contrib.gis.geos import Point

from complaints.models import Complaint
from municipal_services.models import ServiceCategory


class CitizenComplaintForm(forms.ModelForm):
    latitude = forms.FloatField(
        widget=forms.HiddenInput(),
    )

    longitude = forms.FloatField(
        widget=forms.HiddenInput(),
    )

    class Meta:
        model = Complaint
        fields = [
            "service",
            "category",
            "description",
            "photo",
            "address",
        ]

        labels = {
            "service": "الخدمة البلدية",
            "category": "نوع المشكلة",
            "description": "وصف المشكلة",
            "photo": "إرفاق صورة",
            "address": "وصف العنوان",
        }

        widgets = {
            "service": forms.Select(
                attrs={
                    "class": "form-control",
                    "id": "id_service",
                }
            ),
            "category": forms.Select(
                attrs={
                    "class": "form-control",
                    "id": "id_category",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": "اكتب وصفًا واضحًا للمشكلة...",
                }
            ),
            "photo": forms.ClearableFileInput(
    attrs={
        "class": "form-control",
        "accept": "image/*",
    }
),
            "address": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "مثال: شارع الثلاثين، بجوار المدرسة",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["category"].queryset = ServiceCategory.objects.none()

        if "service" in self.data:
            try:
                service_id = int(self.data.get("service"))
                self.fields["category"].queryset = (
                    ServiceCategory.objects.filter(
                        service_id=service_id
                    ).order_by("name_ar")
                )
            except (TypeError, ValueError):
                pass

    def clean(self):
        cleaned_data = super().clean()

        service = cleaned_data.get("service")
        category = cleaned_data.get("category")

        if service and category and category.service_id != service.id:
            self.add_error(
                "category",
                "التصنيف المحدد لا يتبع الخدمة المختارة.",
            )

        return cleaned_data

    def save(self, commit=True):
        complaint = super().save(commit=False)

        latitude = self.cleaned_data["latitude"]
        longitude = self.cleaned_data["longitude"]

        complaint.location = Point(
            longitude,
            latitude,
            srid=4326,
        )

        if commit:
            complaint.save()

        return complaint
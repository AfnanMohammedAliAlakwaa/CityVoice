from django import forms
from django.contrib.gis.geos import Point

from assets.models import MunicipalAsset


class MunicipalAssetForm(forms.ModelForm):
    latitude = forms.DecimalField(
        label="خط العرض",
        max_digits=10,
        decimal_places=7,
        min_value=-90,
        max_value=90,
        widget=forms.NumberInput(
            attrs={
                "step": "0.0000001",
                "placeholder": "15.3694000",
            }
        ),
    )

    longitude = forms.DecimalField(
        label="خط الطول",
        max_digits=10,
        decimal_places=7,
        min_value=-180,
        max_value=180,
        widget=forms.NumberInput(
            attrs={
                "step": "0.0000001",
                "placeholder": "44.1910000",
            }
        ),
    )

    class Meta:
        model = MunicipalAsset

        fields = [
            "asset_code",
            "asset_type",
            "name_ar",
            "neighborhood",
            "address",
            "status",
            "condition",
            "installation_date",
            "notes",
        ]

        labels = {
            "asset_code": "رمز الأصل",
            "asset_type": "نوع الأصل",
            "name_ar": "اسم الأصل",
            "neighborhood": "الحي",
            "address": "العنوان",
            "status": "حالة التشغيل",
            "condition": "الحالة الفنية",
            "installation_date": "تاريخ التركيب",
            "notes": "ملاحظات",
        }

        widgets = {
            "asset_code": forms.TextInput(
                attrs={
                    "placeholder": "مثال: LIGHT-001",
                }
            ),

            "name_ar": forms.TextInput(
                attrs={
                    "placeholder": "اسم مختصر للأصل",
                }
            ),

            "address": forms.TextInput(
                attrs={
                    "placeholder": "وصف موقع الأصل",
                }
            ),

            "installation_date": forms.DateInput(
                attrs={
                    "type": "date",
                }
            ),

            "notes": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "أي ملاحظات إضافية",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk and self.instance.location:
            self.fields["latitude"].initial = (
                self.instance.location.y
            )

            self.fields["longitude"].initial = (
                self.instance.location.x
            )

        for field in self.fields.values():
            existing_class = field.widget.attrs.get(
                "class",
                "",
            )

            field.widget.attrs["class"] = (
                f"{existing_class} mp-form-control"
            ).strip()

    def save(self, commit=True):
        asset = super().save(commit=False)

        latitude = float(
            self.cleaned_data["latitude"]
        )

        longitude = float(
            self.cleaned_data["longitude"]
        )

        asset.location = Point(
            longitude,
            latitude,
            srid=4326,
        )

        if commit:
            asset.save()
            self.save_m2m()

        return asset


class AssetExcelUploadForm(forms.Form):
    excel_file = forms.FileField(
        label="ملف Excel",
        help_text="يُسمح بملفات xlsx فقط.",
        widget=forms.FileInput(
            attrs={
                "accept": (
                    ".xlsx,"
                    "application/vnd.openxmlformats-"
                    "officedocument.spreadsheetml.sheet"
                ),
                "class": "mp-form-control",
            }
        ),
    )

    def clean_excel_file(self):
        excel_file = self.cleaned_data[
            "excel_file"
        ]

        if not excel_file.name.lower().endswith(
            ".xlsx"
        ):
            raise forms.ValidationError(
                "يجب اختيار ملف Excel بصيغة xlsx."
            )

        maximum_size = 5 * 1024 * 1024

        if excel_file.size > maximum_size:
            raise forms.ValidationError(
                "حجم الملف يجب ألا يتجاوز 5 ميجابايت."
            )

        return excel_file
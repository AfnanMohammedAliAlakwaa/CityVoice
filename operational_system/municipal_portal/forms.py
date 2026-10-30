from django import forms
from django.contrib.gis.geos import Point

from assets.models import AssetType, MunicipalAsset
from municipal_services.models import MunicipalService


PRIMARY_ASSET_TYPES = {
    "الإنارة العامة": "عمود إنارة",
    "الطرق والأرصفة": "طريق",
    "المياه والصرف الصحي": "منهل صرف صحي",
    "النظافة وإدارة النفايات": "حاوية نفايات",
}


class MunicipalAssetForm(forms.ModelForm):
    service = forms.ModelChoiceField(
        label="الخدمة",
        queryset=MunicipalService.objects.none(),
        empty_label="اختاري الخدمة",
    )

    latitude = forms.DecimalField(
    label="خط العرض",
    max_digits=12,
    decimal_places=7,
    min_value=-90,
    max_value=90,
    error_messages={
        "required": "يرجى إدخال خط العرض.",
        "invalid": "خط العرض يجب أن يكون رقمًا صحيحًا.",
        "min_value": "خط العرض يجب ألا يقل عن ‎-90.",
        "max_value": "خط العرض يجب ألا يزيد على 90.",
        "max_digits": "عدد خانات خط العرض أكبر من المسموح.",
        "max_decimal_places": (
            "خط العرض يجب ألا يتجاوز 7 أرقام بعد الفاصلة."
        ),
        "max_whole_digits": "قيمة خط العرض كبيرة جدًا.",
    },
    widget=forms.TextInput(
        attrs={
            "inputmode": "decimal",
            "placeholder": "15.3694000",
            "autocomplete": "off",
            }
        ),
    )

    longitude = forms.DecimalField(
    label="خط الطول",
    max_digits=12,
    decimal_places=7,
    min_value=-180,
    max_value=180,
    error_messages={
        "required": "يرجى إدخال خط الطول.",
        "invalid": "خط الطول يجب أن يكون رقمًا صحيحًا.",
        "min_value": "خط الطول يجب ألا يقل عن ‎-180.",
        "max_value": "خط الطول يجب ألا يزيد على 180.",
        "max_digits": "عدد خانات خط الطول أكبر من المسموح.",
        "max_decimal_places": (
            "خط الطول يجب ألا يتجاوز 7 أرقام بعد الفاصلة."
        ),
        "max_whole_digits": "قيمة خط الطول كبيرة جدًا.",
    },
    widget=forms.TextInput(
        attrs={
            "inputmode": "decimal",
            "placeholder": "44.1910000",
            "autocomplete": "off",
            }
        ),
    )

    class Meta:
        model = MunicipalAsset

        fields = [
    "asset_code",
    "service",
    "name_ar",
    "neighborhood",
    "address",
    "status",
    "condition",
    "installation_date",
    "last_maintenance_date",
    "latitude",
    "longitude",
    "notes",
]
        labels = {
            "asset_code": "رمز الأصل",
            "name_ar": "اسم الأصل",
            "neighborhood": "الحي",
            "address": "العنوان",
            "status": "حالة التشغيل",
            "condition": "الحالة الفنية",
            "installation_date": "تاريخ التركيب",
            "last_maintenance_date": "تاريخ آخر صيانة",
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

            "last_maintenance_date": forms.DateInput(
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

        # تحميل الخدمات الفعّالة في القائمة
        if "service" in self.fields:
            self.fields["service"].queryset = (
                MunicipalService.objects
                .filter(is_active=True)
                .order_by("name_ar")
            )

        location = getattr(
            self.instance,
            "location",
            None,
        )

        if self.instance.pk:
            # تحديد خدمة الأصل الحالية عند التعديل
            asset_type = getattr(
                self.instance,
                "asset_type",
                None,
            )

            if (
                "service" in self.fields
                and asset_type is not None
            ):
                self.fields["service"].initial = (
                    asset_type.service_id
                )

            if location is not None:
                self.fields["latitude"].initial = (
                    f"{location.y:.7f}"
                )

                self.fields["longitude"].initial = (
                    f"{location.x:.7f}"
                )

        for field in self.fields.values():
            existing_class = field.widget.attrs.get(
                "class",
                "",
            )

            field.widget.attrs["class"] = (
                f"{existing_class} mp-form-control"
            ).strip()
        def clean(self):
            cleaned_data = super().clean()

            service = cleaned_data.get("service")

            if service:
                asset_type_name = PRIMARY_ASSET_TYPES.get(
                    service.name_ar
            )

            if not asset_type_name:
                self.add_error(
                    "service",
                    "هذه الخدمة غير مهيأة لإضافة الأصول.",
                )

            return cleaned_data

    def save(self, commit=True):
        asset = super().save(commit=False)

        service = self.cleaned_data["service"]

        asset_type_name = PRIMARY_ASSET_TYPES[
            service.name_ar
        ]

        asset_type, unused_created = (
            AssetType.objects.get_or_create(
                service=service,
                name_ar=asset_type_name,
                defaults={
                    "is_active": True,
                },
            )
        )

        if not asset_type.is_active:
            asset_type.is_active = True
            asset_type.save(
                update_fields=["is_active"]
            )

        asset.asset_type = asset_type

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
        help_text="يسمح بملفات xlsx فقط.",
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
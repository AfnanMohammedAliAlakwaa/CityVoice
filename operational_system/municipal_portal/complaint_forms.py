from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q

from assets.models import MunicipalAsset
from complaints.models import Complaint
from maintenance.models import WorkOrder
from municipal_services.models import (
    MunicipalService,
    ServiceCategory,
)


class ServiceRelatedSelect(forms.Select):
    """إضافة رقم الخدمة إلى خيارات التصنيفات والأصول."""

    def create_option(
        self,
        name,
        value,
        label,
        selected,
        index,
        subindex=None,
        attrs=None,
    ):
        option = super().create_option(
            name,
            value,
            label,
            selected,
            index,
            subindex=subindex,
            attrs=attrs,
        )

        instance = getattr(value, "instance", None)

        if isinstance(instance, ServiceCategory):
            option["attrs"]["data-service-id"] = str(
                instance.service_id
            )

        elif isinstance(instance, MunicipalAsset):
            option["attrs"]["data-service-id"] = str(
                instance.asset_type.service_id
            )

        return option


class ComplaintReviewForm(forms.ModelForm):
    """مراجعة بيانات البلاغ واختيار الأولوية يدويًا."""

    class Meta:
        model = Complaint

        fields = [
            "service",
            "category",
            "asset",
            "priority",
        ]

        labels = {
            "service": "الخدمة",
            "category": "تصنيف البلاغ",
            "asset": "الأصل المرتبط بالبلاغ",
            "priority": "أولوية البلاغ",
        }

        widgets = {
            "service": forms.Select(
                attrs={
                    "class": "mc-input",
                    "data-review-service": "true",
                }
            ),
            "category": ServiceRelatedSelect(
                attrs={
                    "class": "mc-input",
                    "data-review-category": "true",
                }
            ),
            "asset": ServiceRelatedSelect(
                attrs={
                    "class": "mc-input",
                    "data-review-asset": "true",
                }
            ),
            "priority": forms.Select(
                attrs={
                    "class": "mc-input",
                }
            ),
        }

        error_messages = {
            "service": {
                "required": "اختر الخدمة.",
                "invalid_choice": "الخدمة المحددة غير متاحة.",
            },
            "category": {
                "required": "اختر تصنيف البلاغ.",
                "invalid_choice": "التصنيف المحدد غير متاح.",
            },
            "asset": {
                "invalid_choice": "الأصل المحدد غير متاح.",
            },
            "priority": {
                "required": "اختر أولوية البلاغ.",
                "invalid_choice": "اختر أولوية من القائمة.",
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        current_service_id = self.instance.service_id
        current_category_id = self.instance.category_id
        current_asset_id = self.instance.asset_id

        self.fields["service"].queryset = (
            MunicipalService.objects.filter(
                Q(is_active=True)
                | Q(pk=current_service_id)
            )
            .order_by("name_ar")
        )

        self.fields["category"].queryset = (
            ServiceCategory.objects.filter(
                Q(
                    is_active=True,
                    service__is_active=True,
                )
                | Q(pk=current_category_id)
            )
            .select_related("service")
            .order_by("service__name_ar", "name_ar")
        )

        # يبقى الأصل المتعطل متاحًا؛ فقد يكون محل البلاغ.
        self.fields["asset"].queryset = (
            MunicipalAsset.objects.filter(
                Q(
                    asset_type__is_active=True,
                    asset_type__service__is_active=True,
                )
                | Q(pk=current_asset_id)
            )
            .select_related(
                "asset_type",
                "asset_type__service",
            )
            .order_by("asset_code")
        )

        self.fields["service"].empty_label = "اختر الخدمة"

        self.fields["category"].empty_label = (
            "اختر تصنيف البلاغ"
        )

        self.fields["asset"].required = False
        self.fields["asset"].empty_label = (
            "لا يوجد أصل مرتبط"
        )

        self.fields["category"].label_from_instance = (
            self.category_label
        )

        self.fields["asset"].label_from_instance = (
            self.asset_label
        )

        self.fields["asset"].help_text = (
            "اختر الأصل الذي تتعلق به المشكلة إن كان مسجلًا."
        )

    @staticmethod
    def category_label(category):
        return (
            f"{category.name_ar}"
            f" — {category.service.name_ar}"
        )

    @staticmethod
    def asset_label(asset):
        asset_name = asset.name_ar.strip()

        title = asset.asset_code

        if asset_name:
            title = f"{title} — {asset_name}"

        return (
            f"{title}"
            f" — {asset.asset_type.service.name_ar}"
        )

    def clean(self):
        cleaned_data = super().clean()

        service = cleaned_data.get("service")
        category = cleaned_data.get("category")
        asset = cleaned_data.get("asset")

        # التحقق في الخادم مستمر حتى بدون JavaScript.
        if service and category:
            if category.service_id != service.pk:
                self.add_error(
                    "category",
                    "اختر تصنيفًا تابعًا للخدمة المحددة.",
                )

        if service and asset:
            if asset.asset_type.service_id != service.pk:
                self.add_error(
                    "asset",
                    "الأصل المحدد يتبع خدمة أخرى. "
                    "اختر أصلًا تابعًا للخدمة المحددة "
                    "أو اختر «لا يوجد أصل مرتبط».",
                )

        return cleaned_data


class ComplaintAssignmentForm(forms.ModelForm):
    """اختيار مستلم أمر العمل وإضافة تعليمات التنفيذ."""

    class Meta:
        model = WorkOrder

        fields = [
            "assigned_to",
            "instructions",
        ]

        labels = {
            "assigned_to": "قائد الفريق",
            "instructions": "تعليمات التنفيذ",
        }

        widgets = {
            "assigned_to": forms.Select(
                attrs={
                    "class": "mc-input",
                }
            ),
            "instructions": forms.Textarea(
                attrs={
                    "class": "mc-input",
                    "rows": 4,
                    "placeholder": (
                        "اكتب التعليمات التي يحتاجها "
                        "قائد الفريق لمعالجة البلاغ."
                    ),
                }
            ),
        }

        error_messages = {
            "assigned_to": {
                "required": "اختر قائد الفريق.",
                "invalid_choice": (
                    "الحساب المحدد غير متاح. "
                    "اختر حسابًا من القائمة."
                ),
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        User = get_user_model()

        # مؤقتًا نعرض حسابات الصيانة النشطة.
        # سيُحصر الاختيار بقادة الفرق بعد إضافة تمييزهم.
        self.fields["assigned_to"].queryset = (
            User.objects.filter(
                role=User.Role.FIELD_WORKER,
                is_active=True,
            )
            .order_by(
                "first_name",
                "last_name",
                "username",
            )
        )

        self.fields["assigned_to"].empty_label = (
            "اختر قائد الفريق"
        )

        self.fields["assigned_to"].label_from_instance = (
            self.worker_label
        )

    @staticmethod
    def worker_label(user):
        full_name = user.get_full_name().strip()

        if full_name:
            return f"{full_name} — {user.username}"

        return user.username

    def clean_instructions(self):
        return (
            self.cleaned_data.get("instructions") or ""
        ).strip()
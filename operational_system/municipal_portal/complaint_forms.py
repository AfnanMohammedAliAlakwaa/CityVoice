from django import forms
from django.db.models import Q

from assets.models import MunicipalAsset
from complaints.models import Complaint
from maintenance.models import MaintenanceTeam, WorkOrder
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
    """اختيار فريق مختص، وتحديد قائده مستلمًا لأمر العمل."""

    class Meta:
        model = WorkOrder

        fields = [
            "team",
            "instructions",
        ]

        labels = {
            "team": "فريق الصيانة",
            "instructions": "تعليمات التنفيذ",
        }

        widgets = {
            "team": forms.Select(
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
                        "فريق الصيانة لمعالجة البلاغ."
                    ),
                }
            ),
        }

        error_messages = {
            "team": {
                "required": "اختر فريق الصيانة.",
                "invalid_choice": (
                    "الفريق المحدد غير متاح لهذه الخدمة. "
                    "اختر فريقًا من القائمة."
                ),
            },
        }

    def __init__(self, *args, complaint=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.complaint = complaint

        if (
            self.complaint is None
            and self.instance.complaint_id
        ):
            self.complaint = self.instance.complaint

        self.fields["team"].required = True
        self.fields["team"].empty_label = (
            "اختر فريق الصيانة"
        )

        self.fields["team"].label_from_instance = (
            self.team_label
        )

        teams = (
            MaintenanceTeam.objects.filter(
                is_active=True,
                service__is_active=True,
                leader__role="field_worker",
                leader__is_active=True,
            )
            .select_related(
                "service",
                "leader",
            )
            .order_by("name")
        )

        if self.complaint is not None:
            self.instance.complaint = self.complaint

            teams = teams.filter(
                service_id=self.complaint.service_id,
            )
        else:
            # يجب أن يمرر الخادم البلاغ للنموذج.
            teams = teams.none()

        self.fields["team"].queryset = teams

    @staticmethod
    def team_label(team):
        leader_name = (
            team.leader.get_full_name().strip()
            or team.leader.get_username()
        )

        return f"{team.name} — القائد: {leader_name}"

    def clean(self):
        cleaned_data = super().clean()

        if self.complaint is None:
            self.add_error(
                None,
                "تعذر تحديد البلاغ المرتبط بالإسناد.",
            )
            return cleaned_data

        team = cleaned_data.get("team")

        if team is None:
            return cleaned_data

        if (
            not team.is_active
            or not team.service.is_active
        ):
            self.add_error(
                "team",
                "الفريق أو خدمته غير نشط.",
            )

        elif team.service_id != self.complaint.service_id:
            self.add_error(
                "team",
                "اختر فريقًا مختصًا بخدمة البلاغ.",
            )

        elif (
            team.leader.role != "field_worker"
            or not team.leader.is_active
        ):
            self.add_error(
                "team",
                "قائد الفريق لا يملك حساب صيانة نشطًا.",
            )

        else:
            # التحديد يتم في الخادم، وليس من حقل يرسله المستخدم.
            self.instance.assigned_to = team.leader

        return cleaned_data

    def clean_instructions(self):
        return (
            self.cleaned_data.get("instructions") or ""
        ).strip()
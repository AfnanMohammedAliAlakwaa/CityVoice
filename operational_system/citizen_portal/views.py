from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from complaints.models import Complaint
from municipal_services.models import ServiceCategory

from .account_forms import CitizenAccountForm
from .forms import CitizenComplaintForm


def citizen_complaints(user):
    return (
        Complaint.objects.filter(citizen=user)
        .select_related("service", "category", "neighborhood")
        .order_by("-created_at", "-pk")
    )


@login_required
def home(request):
    complaints = citizen_complaints(request.user)

    active_statuses = [
        Complaint.Status.SUBMITTED,
        Complaint.Status.UNDER_REVIEW,
        Complaint.Status.ASSIGNED,
        Complaint.Status.IN_PROGRESS,
    ]

    context = {
        "page": "home",
        "recent_complaints": complaints[:3],
        "active_count": complaints.filter(
            status__in=active_statuses
        ).count(),
        "latest_complaint": complaints.first(),
    }

    return render(request, "citizen_portal/home.html", context)


@login_required
def complaint_list(request):
    return render(
        request,
        "citizen_portal/home.html",
        {
            "page": "complaints",
            "complaints": citizen_complaints(request.user),
        },
    )


@login_required
def complaint_detail(request, reference_number):
    complaint = get_object_or_404(
        citizen_complaints(request.user),
        reference_number=reference_number,
    )

    return render(
        request,
        "citizen_portal/home.html",
        {
            "page": "detail",
            "complaint": complaint,
        },
    )


@login_required
def account(request):
    if request.method == "POST":
        form = CitizenAccountForm(
            request.POST,
            request.FILES,
            instance=request.user,
        )

        if form.is_valid():
            form.save()
            return redirect(
                "citizen_portal:account_saved"
            )

    else:
        form = CitizenAccountForm(instance=request.user)

    return render(
        request,
        "citizen_portal/account.html",
        {
            "page": "account",
            "form": form,
            "saved": False,
        },
    )


@login_required
def account_saved(request):
    return render(
        request,
        "citizen_portal/account.html",
        {
            "page": "account",
            "form": CitizenAccountForm(instance=request.user),
            "saved": True,
        },
    )


@login_required
def submit_complaint(request):
    if request.method == "POST":
        uploaded_files = request.FILES.copy()
        camera_photo = uploaded_files.get("camera_photo")

        if camera_photo:
            uploaded_files["photo"] = camera_photo

        form = CitizenComplaintForm(
            request.POST,
            uploaded_files,
        )

        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.citizen = request.user
            complaint.save()

            return redirect(
                "citizen_portal:complaint_success",
                reference_number=complaint.reference_number,
            )

    else:
        form = CitizenComplaintForm()

    return render(
        request,
        "citizen_portal/submit_complaint.html",
        {"form": form},
    )


@login_required
def complaint_success(request, reference_number):
    complaint = get_object_or_404(
        Complaint,
        reference_number=reference_number,
        citizen=request.user,
    )

    return render(
        request,
        "citizen_portal/complaint_success.html",
        {"complaint": complaint},
    )


@login_required
def load_categories(request):
    service_id = request.GET.get("service")

    categories = ServiceCategory.objects.filter(
        service_id=service_id
    ).order_by("name_ar")

    return JsonResponse(
        list(categories.values("id", "name_ar")),
        safe=False,
    )
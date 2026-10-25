from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from complaints.models import Complaint
from municipal_services.models import ServiceCategory

from .forms import CitizenComplaintForm


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

    data = list(
        categories.values(
            "id",
            "name_ar",
        )
    )

    return JsonResponse(data, safe=False)
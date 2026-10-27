import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from .models import District


def main_boundary(request):
    district = get_object_or_404(
        District,
        name_ar="معين",
        is_active=True,
        boundary__isnull=False,
    )

    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "id": district.id,
                    "name_ar": district.name_ar,
                    "name_en": district.name_en,
                },
                "geometry": json.loads(
                    district.boundary.geojson
                ),
            }
        ],
    }

    return JsonResponse(geojson)
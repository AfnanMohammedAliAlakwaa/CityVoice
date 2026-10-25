from django.db import migrations


def seed_initial_services(apps, schema_editor):
    MunicipalService = apps.get_model(
        "municipal_services",
        "MunicipalService",
    )
    ServiceCategory = apps.get_model(
        "municipal_services",
        "ServiceCategory",
    )

    services = [
        {
            "name_ar": "النظافة وإدارة النفايات",
            "name_en": "Waste Management",
            "categories": [
                ("تراكم النفايات", "Waste accumulation"),
                ("حاوية ممتلئة أو تالفة", "Full or damaged bin"),
                ("تأخر جمع النفايات", "Delayed waste collection"),
            ],
        },
        {
            "name_ar": "الطرق والأرصفة",
            "name_en": "Roads and Sidewalks",
            "categories": [
                ("حفرة أو تلف في الطريق", "Pothole or road damage"),
                ("رصيف تالف", "Damaged sidewalk"),
                ("عائق في الطريق", "Road obstruction"),
            ],
        },
        {
            "name_ar": "الإنارة العامة",
            "name_en": "Street Lighting",
            "categories": [
                ("عمود إنارة لا يعمل", "Non-working streetlight"),
                ("عمود إنارة تالف أو آيل للسقوط", "Damaged or leaning pole"),
                ("أسلاك كهربائية مكشوفة", "Exposed electrical wires"),
            ],
        },
        {
            "name_ar": "المياه والصرف الصحي",
            "name_en": "Water and Sewerage",
            "categories": [
                ("تسرب مياه", "Water leak"),
                ("طفح أو انسداد الصرف الصحي", "Sewer overflow or blockage"),
                ("غطاء منهول مفقود أو تالف", "Missing or damaged manhole cover"),
            ],
        },
        {
            "name_ar": "الحدائق والتشجير",
            "name_en": "Parks and Landscaping",
            "categories": [
                ("تلف مرافق الحديقة", "Damaged park facilities"),
                ("شجرة خطرة أو ساقطة", "Dangerous or fallen tree"),
                ("حاجة إلى تقليم أو تشجير", "Pruning or landscaping needed"),
            ],
        },
        {
            "name_ar": "المباني والمرافق العامة",
            "name_en": "Public Buildings and Facilities",
            "categories": [
                ("تلف مرفق عام", "Damaged public facility"),
                ("خطر إنشائي", "Structural hazard"),
                ("نظافة مرفق عام", "Public facility cleanliness"),
            ],
        },
    ]

    for service_data in services:
        service, _ = MunicipalService.objects.update_or_create(
            name_ar=service_data["name_ar"],
            defaults={
                "name_en": service_data["name_en"],
                "is_active": True,
            },
        )

        for category_ar, category_en in service_data["categories"]:
            ServiceCategory.objects.update_or_create(
                service=service,
                name_ar=category_ar,
                defaults={
                    "name_en": category_en,
                    "is_active": True,
                },
            )


class Migration(migrations.Migration):

    dependencies = [
        ("municipal_services", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            seed_initial_services,
            migrations.RunPython.noop,
        ),
    ]
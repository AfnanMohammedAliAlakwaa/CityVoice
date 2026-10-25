from django.db import migrations


ASSET_TYPES = {
    "النظافة وإدارة النفايات": [
        ("حاوية نفايات", "Waste container"),
        ("نقطة تجميع نفايات", "Waste collection point"),
    ],
    "الطرق والأرصفة": [
        ("إشارة مرورية", "Traffic sign"),
        ("حاجز مروري", "Road barrier"),
    ],
    "الإنارة العامة": [
        ("عمود إنارة", "Streetlight pole"),
        ("لوحة توزيع كهربائية", "Electrical distribution panel"),
    ],
    "المياه والصرف الصحي": [
        ("منهل صرف صحي", "Sewer manhole"),
        ("صمام شبكة مياه", "Water network valve"),
    ],
    "الحدائق والتشجير": [
        ("حديقة عامة", "Public park"),
        ("شجرة عامة", "Public tree"),
    ],
    "المباني والمرافق العامة": [
        ("مبنى بلدي", "Municipal building"),
        ("مرفق عام", "Public facility"),
    ],
}


def create_asset_types(apps, schema_editor):
    MunicipalService = apps.get_model(
        "municipal_services",
        "MunicipalService",
    )
    AssetType = apps.get_model("assets", "AssetType")

    for service_name, asset_types in ASSET_TYPES.items():
        service = MunicipalService.objects.get(name_ar=service_name)

        for name_ar, name_en in asset_types:
            AssetType.objects.get_or_create(
                service=service,
                name_ar=name_ar,
                defaults={
                    "name_en": name_en,
                    "is_active": True,
                },
            )


def remove_asset_types(apps, schema_editor):
    AssetType = apps.get_model("assets", "AssetType")

    for asset_types in ASSET_TYPES.values():
        names = [name_ar for name_ar, name_en in asset_types]
        AssetType.objects.filter(name_ar__in=names).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("assets", "0001_initial"),
        ("municipal_services", "0002_seed_initial_services"),
    ]

    operations = [
        migrations.RunPython(
            create_asset_types,
            remove_asset_types,
        ),
    ]
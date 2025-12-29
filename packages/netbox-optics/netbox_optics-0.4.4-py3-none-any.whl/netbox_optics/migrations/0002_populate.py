from decimal import Decimal

from django.db import migrations


GRID_DEFINITIONS = (
    (
        "DWDM 100GHz",
        100,
        "Standard DWDM grid with 100GHz spacing",
        tuple(
            "1528.77 1529.55 1530.33 1531.12 1531.9 1532.68 1533.47 1534.25 1535.04 "
            "1535.82 1536.61 1537.4 1538.19 1538.98 1539.77 1540.56 1541.35 1542.14 "
            "1542.94 1543.73 1544.53 1545.32 1546.12 1546.92 1547.72 1548.51 1549.32 "
            "1550.12 1550.92 1551.72 1552.52 1553.33 1554.13 1554.94 1555.75 1556.55 "
            "1557.36 1558.17 1558.98 1559.79 1560.61 1561.42 1562.23 1563.05 1563.86 "
            "1564.68 1565.5 1566.31 1567.13 1567.95 1568.77".split()
        ),
    ),
    (
        "DWDM 75GHz",
        75,
        "DWDM grid with 75GHz spacing",
        tuple(
            "1537 1528.77 1529.36 1529.94 1530.53 1531.12 1531.7 1532.29 1532.88 1533.47 "
            "1534.05 1534.64 1535.23 1535.82 1536.41 1537.59 1538.19 1538.78 1539.37 1539.96 "
            "1540.56 1541.15 1541.75 1542.34 1542.94 1543.53 1544.13 1544.72 1545.32 1545.92 "
            "1546.52 1547.12 1547.72 1548.31 1548.91 1549.52 1550.12 1550.72 1551.32 1551.92 "
            "1552.52 1553.13 1553.73 1554.34 1554.94 1555.55 1556.15 1556.76 1557.36 1557.97 "
            "1558.58 1559.19 1559.79 1560.4 1561.01 1561.62 1562.23 1562.84 1563.45 1564.07 "
            "1564.68 1565.29 1565.9 1566.52".split()
        ),
    ),
    (
        "DWDM 50GHz",
        50,
        "DWDM grid with 50GHz spacing",
        tuple(
            "1537 1528.77 1529.16 1529.55 1529.94 1530.33 1530.72 1531.12 1531.51 1531.9 "
            "1532.29 1532.68 1533.07 1533.47 1533.86 1534.25 1534.64 1535.04 1535.43 1535.82 "
            "1536.22 1536.61 1537.4 1537.79 1538.19 1538.58 1538.98 1539.37 1539.77 1539.96 "
            "1540.16 1540.56 1540.95 1541.35 1541.75 1542.14 1542.54 1542.94 1543.33 1543.73 "
            "1544.13 1544.53 1544.92 1545.32 1545.72 1546.12 1546.52 1546.92 1547.32 1547.72 "
            "1548.11 1548.51 1548.91 1549.32 1549.72 1550.12 1550.52 1550.92 1551.32 1551.72 "
            "1552.12 1552.52 1552.93 1553.33 1553.73 1554.13 1554.54 1554.94 1555.34 1555.75 "
            "1556.15 1556.55 1556.96 1557.36 1557.77 1558.17 1558.58 1558.98 1559.39 1559.79 "
            "1560.2 1560.61 1561.01 1561.42 1561.83 1562.23 1562.64 1563.05 1563.45 1563.86 "
            "1564.27 1564.68 1565.09 1565.5 1565.9 1566.31 1566.72 1567.13 1567.54 1567.95 1568.36".split()
        ),
    ),
)


def add_initial_data(apps, schema_editor):
    OpticalGridType = apps.get_model("netbox_optics", "OpticalGridType")
    OpticalGridTypeWavelength = apps.get_model(
        "netbox_optics", "OpticalGridTypeWavelength"
    )

    for name, spacing, description, wavelengths in GRID_DEFINITIONS:
        grid_type, created = OpticalGridType.objects.get_or_create(
            name=name,
            defaults={
                "spacing": spacing,
                "description": description,
            },
        )

        if not created:
            update_fields = []
            if grid_type.spacing != spacing:
                grid_type.spacing = spacing
                update_fields.append("spacing")
            if grid_type.description != description:
                grid_type.description = description
                update_fields.append("description")
            if update_fields:
                grid_type.save(update_fields=update_fields)

        for wavelength in wavelengths:
            OpticalGridTypeWavelength.objects.get_or_create(
                grid_type=grid_type,
                value=Decimal(wavelength),
            )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("netbox_optics", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(add_initial_data, noop),
    ]



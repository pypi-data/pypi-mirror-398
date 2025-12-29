"""Tables used to display list views of models"""

import django_tables2 as tables
from netbox.tables import NetBoxTable, columns
from django.urls import reverse
from django.utils.html import format_html
from .models import (
    OpticalGridType,
    OpticalGrid,
    OpticalGridWavelength,
    OpticalGridTypeWavelength,
    OpticalSpan,
    OpticalConnection,
    MuxWavelengthMap,
)


class OpticalGridTypeTable(NetBoxTable):
    # make row selectable
    pk = columns.ToggleColumn()
    # make id column link to detail view
    id = tables.Column(linkify=True, verbose_name="ID")
    # make name column link to detail view
    name = tables.Column(linkify=True)
    spacing = tables.Column()
    grids = tables.Column(verbose_name="Grids", accessor="grids_count")

    def render_grids(self, record):
        count = getattr(record, "grids_count", 0)
        url = (
            reverse("plugins:netbox_optics:opticalgrid_list")
            + f"?grid_type={record.id}"
        )
        return format_html('<a href="{}">{}</a>', url, count)

    class Meta(NetBoxTable.Meta):
        model = OpticalGridType
        fields = ["pk", "id", "name", "spacing", "grids"]
        default_columns = ["id", "name", "spacing", "grids"]


class OpticalGridTable(NetBoxTable):
    pk = columns.ToggleColumn()
    id = tables.Column(linkify=True, verbose_name="ID")
    name = tables.Column(linkify=True)
    grid_type = tables.Column(linkify=True, verbose_name="Grid Type")
    spacing = tables.Column()

    class Meta(NetBoxTable.Meta):
        model = OpticalGrid
        fields = ["pk", "id", "name", "grid_type", "spacing"]
        default_columns = ["id", "name", "grid_type", "spacing"]


class OpticalGridWavelengthTable(NetBoxTable):
    pk = columns.ToggleColumn()
    id = tables.Column(linkify=True, verbose_name="ID")
    grid = tables.Column(linkify=True, verbose_name="Optical Grid")
    value = tables.Column(verbose_name="Wavelength (nm)")

    class Meta(NetBoxTable.Meta):
        model = OpticalGridWavelength
        fields = ["pk", "id", "grid", "value"]
        default_columns = ["id", "grid", "value"]


class OpticalGridTypeWavelengthTable(NetBoxTable):
    pk = columns.ToggleColumn()
    id = tables.Column(linkify=True, verbose_name="ID")
    grid_type = tables.Column(linkify=True, verbose_name="Grid Type")
    value = tables.Column(verbose_name="Wavelength")
    actions = columns.ActionsColumn(actions=("edit", "changelog"))

    class Meta(NetBoxTable.Meta):
        model = OpticalGridTypeWavelength
        fields = ["pk", "id", "grid_type", "value"]
        default_columns = ["id", "grid_type", "value"]


class OpticalSpanTable(NetBoxTable):
    pk = columns.ToggleColumn()
    id = tables.Column(linkify=True, verbose_name="ID")
    name = tables.Column(linkify=True)
    site_a = tables.Column(linkify=True, verbose_name="Site A")
    site_b = tables.Column(linkify=True, verbose_name="Site B")
    grid = tables.Column(linkify=True, verbose_name="Optical Grid")
    mux_a = tables.Column(linkify=True, verbose_name="Mux A")
    mux_z = tables.Column(linkify=True, verbose_name="Mux Z")
    connections = tables.Column(
        verbose_name="Connections", accessor="connections_count"
    )
    free_wavelengths = tables.Column(
        verbose_name="Free Wavelengths", empty_values=(), orderable=False
    )
    used_wavelengths = tables.Column(
        verbose_name="Used Wavelengths", empty_values=(), orderable=False
    )

    def render_connections(self, value, record):
        count = getattr(record, "connections_count", 0)
        url = (
            reverse("plugins:netbox_optics:opticalconnection_list")
            + f"?span_id={record.id}"
        )
        return format_html('<a href="{}">{}</a>', url, count)

    def render_free_wavelengths(self, value, record):
        # Link to wavelengths list filtered by this span and free status
        url = (
            reverse("plugins:netbox_optics:opticalgridwavelength_list")
            + f"?span={record.id}&status=free"
        )
        # We won't precompute count server-side now; leave as link-only for simplicity/perf
        return format_html('<a href="{}">Show</a>', url)

    def render_used_wavelengths(self, value, record):
        # Link to wavelengths list filtered by this span and reserved status
        url = (
            reverse("plugins:netbox_optics:opticalgridwavelength_list")
            + f"?span={record.id}&status=reserved"
        )
        return format_html('<a href="{}">Show</a>', url)

    class Meta(NetBoxTable.Meta):
        model = OpticalSpan
        fields = [
            "id",
            "pk",
            "name",
            "site_a",
            "site_b",
            "grid",
            "mux_a",
            "mux_z",
            "connections",
            "free_wavelengths",
            "used_wavelengths",
            "vendor_circuit_id",
            "vendor",
        ]
        default_columns = [
            "id",
            "name",
            "site_a",
            "site_b",
            "grid",
            "mux_a",
            "mux_z",
            "connections",
            "free_wavelengths",
            "vendor_circuit_id",
            "vendor",
        ]


class OpticalConnectionTable(NetBoxTable):
    pk = columns.ToggleColumn()
    id = tables.Column(linkify=True, verbose_name="ID")
    name = tables.Column(linkify=True)
    span = tables.Column(linkify=True)
    site_a = tables.Column(accessor="span.site_a", linkify=True, verbose_name="Site A")
    site_b = tables.Column(accessor="span.site_b", linkify=True, verbose_name="Site B")
    wavelength = tables.Column(accessor="wavelength.value", verbose_name="Wavelength")
    mux_a = tables.Column(accessor="span.mux_a", linkify=True, verbose_name="Mux A")
    mux_z = tables.Column(accessor="span.mux_z", linkify=True, verbose_name="Mux Z")
    interface_a = tables.Column(linkify=True, verbose_name="Interface A")
    interface_z = tables.Column(linkify=True, verbose_name="Interface Z")
    device_a = tables.Column(
        accessor="interface_a.device", linkify=True, verbose_name="Device A"
    )
    device_z = tables.Column(
        accessor="interface_z.device", linkify=True, verbose_name="Device Z"
    )

    class Meta(NetBoxTable.Meta):
        model = OpticalConnection
        fields = [
            "id",
            "pk",
            "name",
            "span",
            "wavelength",
            "mux_a",
            "mux_z",
            "tx_power",
            "device_a",
            "interface_a",
            "device_z",
            "interface_z",
            "site_a",
            "site_b",
        ]
        default_columns = [
            "id",
            "name",
            "span",
            "wavelength",
            "mux_a",
            "mux_z",
            "device_a",
            "interface_a",
            "device_z",
            "interface_z",
            "site_a",
            "site_b",
        ]


class MuxWavelengthMapTable(NetBoxTable):
    pk = columns.ToggleColumn()
    id = tables.Column(linkify=True, verbose_name="ID")
    mux = tables.Column(linkify=True, verbose_name="Mux Device")
    port = tables.Column(linkify=True, verbose_name="Port")
    wavelength = tables.Column(accessor="wavelength.value", verbose_name="Wavelength")
    grid = tables.Column(accessor="wavelength.grid", linkify=True, verbose_name="Grid")

    class Meta(NetBoxTable.Meta):
        model = MuxWavelengthMap
        fields = [
            "id",
            "pk",
            "mux",
            "port",
            "wavelength",
            "grid",
        ]
        default_columns = [
            "id",
            "mux",
            "port",
            "wavelength",
            "grid",
        ]

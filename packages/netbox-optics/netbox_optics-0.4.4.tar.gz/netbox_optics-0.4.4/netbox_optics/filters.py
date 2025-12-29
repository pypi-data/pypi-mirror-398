import django_filters
from django.db.models import Q
from rest_framework.exceptions import ValidationError

from netbox.filtersets import NetBoxModelFilterSet
from utilities.filters import (
    MultiValueNumberFilter,
    MultiValueDecimalFilter,
    MultiValueCharFilter,
)
from dcim.models import Interface, Device, Site

from .models import (
    OpticalGridType,
    OpticalGrid,
    OpticalGridWavelength,
    OpticalGridTypeWavelength,
    OpticalSpan,
    OpticalConnection,
    MuxWavelengthMap,
)

# todo add NetBoxModelFilterSetForm for gui
import logging

logger = logging.getLogger()


class OpticalGridTypeFilter(NetBoxModelFilterSet):
    q = django_filters.CharFilter(
        method="search",
        label="Search",
    )
    spacing = MultiValueNumberFilter()  # todo positive integer

    def search(self, queryset, name, value):
        value = value.strip()
        if not value:
            return queryset
        return queryset.filter(Q(name__icontains=value))

    class Meta:
        model = OpticalGridType
        fields = ["id"]


class OpticalGridFilter(NetBoxModelFilterSet):
    q = django_filters.CharFilter(
        method="search",
        label="Search",
    )
    grid_type = django_filters.ModelMultipleChoiceFilter(
        queryset=OpticalGridType.objects.all(),
        label="Grid Type",
    )
    spacing = MultiValueNumberFilter()

    def search(self, queryset, name, value):
        value = value.strip()
        if not value:
            return queryset
        return queryset.filter(
            Q(name__icontains=value)
            | Q(description__icontains=value)
            | Q(grid_type__name__icontains=value)
        ).distinct()

    class Meta:
        model = OpticalGrid
        fields = ["id"]


class OpticalGridWavelengthFilter(NetBoxModelFilterSet):
    q = django_filters.CharFilter(
        method="search",
        label="Search",
    )
    grid = django_filters.ModelMultipleChoiceFilter(
        queryset=OpticalGrid.objects.all(),
        label="Optical Grid",
    )
    span = django_filters.ModelMultipleChoiceFilter(
        queryset=OpticalSpan.objects.all(),
        method="filter_by_span",
        label="Optical Span",
    )

    status = django_filters.MultipleChoiceFilter(
        choices=(
            ("free", "Free"),
            ("reserved", "Reserved"),
        ),
        method="filter_by_status",
        label="Status (requires span)",
    )

    value = MultiValueDecimalFilter()

    def search(self, queryset, name, value):
        value = value.strip()
        if not value:
            return queryset
        return queryset.filter(
            Q(value__icontains=value) | Q(grid__name__icontains=value)
        ).distinct()

    def filter_by_span(self, queryset, name, value):
        """Filter wavelengths by span's grid"""
        if value:
            grid_ids = [span.grid.id for span in value if span.grid]
            return queryset.filter(grid_id__in=grid_ids)
        return queryset

    def filter_by_status(self, queryset, name, value):
        """Filter wavelengths by reservation status for a given span.
        Expects a single span id via ?span=<id>. If both statuses passed, no-op.
        """
        if not value:
            return queryset

        # Get span id from request params
        span_ids = self.data.getlist("span") or self.data.getlist("span_id")
        if not span_ids:
            return queryset
        try:
            span_id = int(span_ids[0])
        except (TypeError, ValueError):
            return queryset

        try:
            span = OpticalSpan.objects.get(pk=span_id)
        except OpticalSpan.DoesNotExist:
            return queryset

        # Scope to the span's grid first
        queryset = queryset.filter(grid=span.grid)

        values = set(value)
        has_free = "free" in values
        has_reserved = "reserved" in values

        if has_free and not has_reserved:
            return queryset.exclude(connections__span=span)
        if has_reserved and not has_free:
            return queryset.filter(connections__span=span).distinct()
        # both selected -> return all
        return queryset

    class Meta:
        model = OpticalGridWavelength
        fields = ["id", "grid", "value"]


class OpticalGridTypeWavelengthFilter(NetBoxModelFilterSet):
    q = django_filters.CharFilter(
        method="search",
        label="Search",
    )
    grid_type = django_filters.ModelMultipleChoiceFilter(
        queryset=OpticalGridType.objects.all(),
        label="Grid Type",
    )
    value = MultiValueDecimalFilter()

    def search(self, queryset, name, value):
        value = value.strip()
        if not value:
            return queryset
        return queryset.filter(
            Q(value__icontains=value) | Q(grid_type__name__icontains=value)
        ).distinct()

    class Meta:
        model = OpticalGridTypeWavelength
        fields = ["id"]


# todo mb filter by by full/empty span
class OpticalSpanFilter(NetBoxModelFilterSet):
    q = django_filters.CharFilter(
        method="search",
        label="Search",
    )
    site = django_filters.ModelMultipleChoiceFilter(
        field_name="site_a",
        queryset=Site.objects.all(),
        method="filter_by_site",
        label="Site",
    )
    site_ids = MultiValueCharFilter(
        method="filter_by_site_ids",
        label="Site IDs (two, comma-separated)",
    )
    vendor_circuit_id = django_filters.CharFilter(lookup_expr="exact")
    vendor_circuit_id__ic = django_filters.CharFilter(
        lookup_expr="icontains", label="Vendor circuit ID (contains)"
    )
    vendor = django_filters.CharFilter(lookup_expr="exact")
    vendor__ic = django_filters.CharFilter(
        lookup_expr="icontains", label="Vendor (contains)"
    )
    # spacing = NumericInFilter(lookup_expr='exact') # todo
    grid = django_filters.ModelMultipleChoiceFilter(
        queryset=OpticalGrid.objects.all(),
        label="Optical Grid",
    )

    def search(self, queryset, name, value):
        value = value.strip()
        if not value:
            return queryset
        return queryset.filter(
            Q(vendor_circuit_id__icontains=value)
            | Q(site_a__name__icontains=value)
            | Q(site_b__name__icontains=value)
            | Q(name__icontains=value)
            | Q(description__icontains=value)
            | Q(vendor__icontains=value)
        ).distinct()

    def filter_by_site(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(Q(site_a__in=value) | Q(site_b__in=value)).distinct()

    def filter_by_site_ids(self, queryset, name, value):
        """
        Filter by two connected sites - comma-separated, or by terminating site. Multiple values ORed.
        """
        if not value:
            return queryset

        filters = Q()

        for param in value:
            sites = param.split(",")  # Assume format "City1_id,City2_id"

            if len(sites) > 2:
                raise ValidationError({"error": "Filter accepts exactly 2 sites maximum"})

            try:
                site_ids = [int(site) for site in sites]
            except ValueError:
                raise ValidationError({"error": f"Invalid site IDs in {param}"})

            if len(site_ids) == 2:
                filters |= Q(site_a__id=site_ids[0], site_b__id=site_ids[1]) | Q(
                    site_a__id=site_ids[1], site_b__id=site_ids[0]
                )
            else:
                filters |= Q(site_a__id=site_ids[0]) | Q(site_b__id=site_ids[0])

        return queryset.filter(filters)

    class Meta:
        model = OpticalSpan
        fields = ["id"]


class OpticalConnectionFilter(NetBoxModelFilterSet):
    q = django_filters.CharFilter(
        method="search",
        label="Search",
    )
    span_id = django_filters.ModelMultipleChoiceFilter(
        field_name='span',
        queryset=OpticalSpan.objects.all(),
        label="Optical Span (ID)",
    )
    site_a_id = django_filters.ModelMultipleChoiceFilter(
        field_name="span__site_a",
        queryset=Site.objects.all(),
        label="Site A (ID)",
    )
    site_b_id = django_filters.ModelMultipleChoiceFilter(
        field_name="span__site_b",
        queryset=Site.objects.all(),
        label="Site B (ID)",
    )
    # todo filter by slug span
    interface_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Interface.objects.all(),
        method="filter_by_interface_id",
        label="Interface (ID)",
        help_text="Filter where interface_a OR interface_z matches any provided values",
    )
    device_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Device.objects.all(),
        method="filter_by_device_id",
        label="Device (ID)",
        help_text="Filter where device_a OR device_z matches any provided values",
    )

    wavelength_id = django_filters.ModelMultipleChoiceFilter(
        field_name='wavelength',
        queryset=OpticalGridWavelength.objects.all(),
        label="Wavelength (ID)",
    )
    wavelength = MultiValueDecimalFilter(
        field_name='wavelength__value',
        label="Wavelength Value",
    )
    vendor_circuit_id = django_filters.CharFilter(
        field_name="span__vendor_circuit_id",
        lookup_expr="exact",
        label="Vendor Circuit ID",
    )
    tx_power = MultiValueNumberFilter()

    def filter_by_interface_id(self, queryset, name, value):
        """
        Filter where interface_a OR interface_z matches any provided values
        """
        if not value:
            return queryset

        return queryset.filter(Q(interface_a__in=value) | Q(interface_z__in=value))

    def filter_by_device_id(self, queryset, name, value):
        """
        Filter where device_a OR device_z matches any provided values
        """
        if not value:
            return queryset

        return queryset.filter(
            Q(interface_a__device__in=value) | Q(interface_z__device__in=value)
        )

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value)
            | Q(description__icontains=value)
            | Q(interface_a__device__name__icontains=value)
            | Q(interface_z__device__name__icontains=value)
        )

    class Meta:
        model = OpticalConnection
        fields = ["id"]


class MuxWavelengthMapFilter(NetBoxModelFilterSet):
    q = django_filters.CharFilter(
        method="search",
        label="Search",
    )
    mux_id = django_filters.ModelMultipleChoiceFilter(
        field_name='mux',
        queryset=Device.objects.all(),
        label="Mux Device (ID)",
    )
    wavelength_id = django_filters.ModelMultipleChoiceFilter(
        field_name='wavelength',
        queryset=OpticalGridWavelength.objects.all(),
        label="Wavelength (ID)",
    )
    span_id = django_filters.ModelMultipleChoiceFilter(
        queryset=OpticalSpan.objects.all(),
        method="filter_by_span",
        label="Span (ID)",
    )

    def filter_by_span(self, queryset, name, value):
        """
        Filter by spans that use the same grid as the wavelength
        """
        if not value:
            return queryset
        return queryset.filter(wavelength__grid__spans__in=value)

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(mux__name__icontains=value)
            | Q(port__name__icontains=value)
            | Q(wavelength__value__icontains=value)
        )

    class Meta:
        model = MuxWavelengthMap
        fields = ["id"]

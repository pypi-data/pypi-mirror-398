from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.core.exceptions import ValidationError
from decimal import Decimal, InvalidOperation

from netbox.forms import NetBoxModelForm, NetBoxModelImportForm, NetBoxModelFilterSetForm
from utilities.forms import BOOLEAN_WITH_BLANK_CHOICES
from utilities.forms.fields import (
    DynamicModelChoiceField,
    DynamicModelMultipleChoiceField,
    CSVModelChoiceField,
)
from utilities.forms.widgets import APISelect, APISelectMultiple
from dcim.models import Device, Site

from .models import (
    OpticalGridType,
    OpticalGrid,
    OpticalGridWavelength,
    OpticalGridTypeWavelength,
    OpticalSpan,
    OpticalConnection,
    MuxWavelengthMap,
    Interface,
)
from .constants import MUX_ROLE_SLUG


class OpticalGridTypeForm(NetBoxModelForm):
    spacing = forms.IntegerField(
        required=True,
        min_value=1,
        label="Spacing",
        help_text="Wavelength spacing in GHz.",
    )
    class Meta:
        model = OpticalGridType
        fields = ["name", "spacing", "description"]


class OpticalGridTypeFilterForm(NetBoxModelFilterSetForm):
    """Form for filtering OpticalGridType instances."""

    model = OpticalGridType
    q = forms.CharField(required=False, label="Search")
    spacing = forms.MultipleChoiceField(
        choices=[("", "Select Spacing")],  # Empty choices initially
        required=False,
        label="Spacing",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        spacings = (
            OpticalGridType.objects.order_by("spacing")
            .values_list("spacing", flat=True)
            .distinct()
        )
        self.fields["spacing"].choices += [(s, f"{s} GHz") for s in spacings]


class OpticalGridTypeImportForm(NetBoxModelImportForm):
    class Meta:
        model = OpticalGridType
        fields = ["name", "spacing", "description"]


class BaseOpticalGridTypeWavelengthFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()

        # Check for duplicate wavelengths
        wavelengths = []
        # todo early loop continue
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get("DELETE", False):
                value = form.cleaned_data.get("value")
                if value:
                    if value in wavelengths:
                        raise ValidationError(
                            f"Duplicate wavelength value: {value}. Each wavelength must be unique."
                        )
                    wavelengths.append(value)


OpticalGridWavelengthFormSet = inlineformset_factory(
    OpticalGrid,
    OpticalGridWavelength,
    fields=["value"],
    extra=3,  # Allows 3 empty forms for new wavelengths
    can_delete=True,
    widgets={
        "value": forms.NumberInput(
            attrs={"step": "0.01", "min": "0.01", "placeholder": "Wavelength (nm)"}
        ),
    },
)

# Formset for existing objects (fewer extra forms)
OpticalGridTypeWavelengthFormSet = inlineformset_factory(
    OpticalGridType,
    OpticalGridTypeWavelength,
    fields=["value"],
    extra=3,  # Allows 3 empty forms for existing objects
    can_delete=True,
    formset=BaseOpticalGridTypeWavelengthFormSet,
    widgets={
        "value": forms.NumberInput(
            attrs={"step": "0.01", "min": "0.01", "placeholder": "Wavelength (nm)"}
        ),
    },
)

# Formset for new objects (more extra forms)
OpticalGridTypeWavelengthFormSetNew = inlineformset_factory(
    OpticalGridType,
    OpticalGridTypeWavelength,
    fields=["value"],
    extra=20,  # Allows 20 empty forms for new objects
    can_delete=True,
    formset=BaseOpticalGridTypeWavelengthFormSet,
    widgets={
        "value": forms.NumberInput(
            attrs={"step": "0.01", "min": "0.01", "placeholder": "Wavelength (nm)"}
        ),
    },
)


class BulkWavelengthForm(forms.Form):
    """Form for bulk wavelength input via comma-separated values"""

    bulk_wavelengths = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "placeholder": "Enter wavelengths separated by commas (e.g., 1550.12, 1550.92, 1551.72)",
                "class": "form-control",
            }
        ),
        help_text="Enter wavelength values separated by commas or comma+space. Values should be in nm.",
    )

    def clean_bulk_wavelengths(self):
        """Parse comma-separated wavelengths and validate them"""
        data = self.cleaned_data["bulk_wavelengths"]
        if not data.strip():
            return []

        # Split by comma and clean whitespace
        values = [v.strip() for v in data.split(",") if v.strip()]

        validated_values = []
        for i, value in enumerate(values, 1):
            try:
                decimal_value = Decimal(value)
                if decimal_value <= 0:
                    raise ValidationError(
                        f"Wavelength {value} at position {i} must be positive"
                    )
                validated_values.append(decimal_value)
            except InvalidOperation:
                raise ValidationError(
                    f"Invalid wavelength value '{value}' at position {i}"
                )

        return validated_values


class OpticalGridForm(NetBoxModelForm):
    grid_type = DynamicModelChoiceField(
        queryset=OpticalGridType.objects.all(),
        required=True,
        label="Grid Type",
        widget=APISelect(api_url="/api/plugins/optics/optical-grid-types/"),
        help_text="Grid type template this instance is based on",
    )

    class Meta:
        model = OpticalGrid
        fields = ["name", "grid_type", "description"]
        help_texts = {
            "name": "Name of the grid instance (optional, will use grid type name if empty)",
            "description": "Description of the grid (optional, will use grid type description if empty)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # grid_type is init only param
        if self.instance and self.instance.pk:
            self.fields["grid_type"].disabled = True


class OpticalGridFilterForm(NetBoxModelFilterSetForm):
    """Form for filtering OpticalGrid instances."""

    model = OpticalGrid
    q = forms.CharField(required=False, label="Search")
    grid_type = DynamicModelMultipleChoiceField(
        queryset=OpticalGridType.objects.all(),
        required=False,
        label="Grid Type",
        widget=APISelectMultiple(api_url="/api/plugins/optics/optical-grid-types/"),
    )
    spacing = forms.MultipleChoiceField(
        choices=[("", "Select Spacing")],  # Empty choices initially
        required=False,
        label="Spacing",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Update spacing choices dynamically
        spacings = (
            OpticalGrid.objects.order_by("spacing")
            .values_list("spacing", flat=True)
            .distinct()
        )
        self.fields["spacing"].choices += [(s, f"{s} GHz") for s in spacings]


class OpticalGridImportForm(NetBoxModelImportForm):
    grid_type = CSVModelChoiceField(
        queryset=OpticalGridType.objects.all(), required=True
    )

    class Meta:
        model = OpticalGrid
        fields = ["name", "grid_type", "description"]


class OpticalGridWavelengthForm(NetBoxModelForm):
    grid = DynamicModelChoiceField(
        queryset=OpticalGrid.objects.all(),
        required=True,
        label="Optical Grid",
        widget=APISelect(api_url="/api/plugins/optics/optical-grids/"),
        help_text="Optical grid this wavelength belongs to",
    )
    value = forms.DecimalField(
        max_digits=6,
        decimal_places=2,
        required=True,
        help_text="Wavelength value in nanometers",
    )

    class Meta:
        model = OpticalGridWavelength
        fields = ["grid", "value"]


class OpticalGridTypeWavelengthForm(NetBoxModelForm):
    grid_type = DynamicModelChoiceField(
        queryset=OpticalGridType.objects.all(),
        required=True,
        label="Grid Type",
        widget=APISelect(api_url="/api/plugins/optics/optical-grid-types/"),
    )

    class Meta:
        model = OpticalGridTypeWavelength
        fields = ["grid_type", "value"]


class OpticalGridWavelengthFilterForm(NetBoxModelFilterSetForm):
    """Form for filtering OpticalGridWavelength instances."""

    model = OpticalGridWavelength
    q = forms.CharField(required=False, label="Search")
    grid = DynamicModelMultipleChoiceField(
        queryset=OpticalGrid.objects.all(),
        required=False,
        label="Optical Grid",
        widget=APISelectMultiple(api_url="/api/plugins/optics/optical-grids/"),
        help_text="Filter by optical grid",
    )
    value = forms.DecimalField(required=False, label="Wavelength Value")


class OpticalGridTypeWavelengthFilterForm(NetBoxModelFilterSetForm):
    """Form for filtering OpticalGridTypeWavelength instances."""

    model = OpticalGridTypeWavelength
    q = forms.CharField(required=False, label="Search")
    grid_type = DynamicModelMultipleChoiceField(
        queryset=OpticalGridType.objects.all(),
        required=False,
        label="Grid Type",
        widget=APISelectMultiple(api_url="/api/plugins/optics/optical-grid-types/"),
    )
    value = forms.DecimalField(required=False, label="Wavelength Value")


class OpticalGridWavelengthImportForm(NetBoxModelImportForm):
    grid = CSVModelChoiceField(queryset=OpticalGrid.objects.all(), required=True)

    class Meta:
        model = OpticalGridWavelength
        fields = ["grid", "value"]


class OpticalSpanForm(NetBoxModelForm):
    site_a = DynamicModelChoiceField(
        queryset=Site.objects.all(),
        required=True,
        label="Site A",
        help_text="First site of the optical span",
    )
    site_b = DynamicModelChoiceField(
        queryset=Site.objects.all(),
        required=True,
        label="Site B",
        help_text="Remote site of the optical span",
    )
    grid = DynamicModelChoiceField(
        queryset=OpticalGrid.objects.all(),
        required=True,
        label="Optical Grid",
        widget=APISelect(api_url="/api/plugins/optics/optical-grids/"),
        help_text="Optical grid defining wavelengths for this span",
    )
    mux_a = DynamicModelChoiceField(
        queryset=Device.objects.all(),
        required=False,
        label="Mux A",
        query_params={"site_id": "$site_a", "role": MUX_ROLE_SLUG},
        help_text="Mux device at site A (Device with role=mux)",
    )
    mux_z = DynamicModelChoiceField(
        queryset=Device.objects.all(),
        required=False,
        label="Mux Z",
        query_params={"site_id": "$site_b", "role": MUX_ROLE_SLUG},
        help_text="Mux device at site Z (Device with role=mux)",
    )

    class Meta:
        model = OpticalSpan
        fields = [
            "name",
            "site_a",
            "site_b",
            "grid",
            "mux_a",
            "mux_z",
            "vendor_circuit_id",
            "vendor",
            "description",
        ]
        help_texts = {
            "vendor_circuit_id": "Unique identifier for the circuit",
            "vendor": "Name of the vendor providing the circuit",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # grid is init only param
        if self.instance and self.instance.pk:
            self.fields["grid"].disabled = True


class OpticalSpanFilterForm(NetBoxModelFilterSetForm):
    """Form for filtering OpticalSpan instances."""

    model = OpticalSpan
    q = forms.CharField(required=False, label="Search")
    site = DynamicModelMultipleChoiceField(
        queryset=Site.objects.all(), required=False, label="Site"
    )
    vendor_circuit_id = forms.ChoiceField(
        choices=[("", "Select Vendor Circuit ID")],  # Empty choices initially
        required=False,
        label="Vendor Circuit ID",
    )
    vendor = forms.ChoiceField(
        choices=[("", "Select Vendor")],  # Empty choices initially
        required=False,
        label="Vendor",
    )
    grid = DynamicModelMultipleChoiceField(
        queryset=OpticalGrid.objects.all(),
        required=False,
        label="Optical Grid",
        widget=APISelectMultiple(api_url="/api/plugins/optics/optical-grids/"),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Update vendor_circuit_id choices dynamically
        vendor_circuit_ids = (
            OpticalSpan.objects.order_by("vendor_circuit_id")
            .values_list("vendor_circuit_id", flat=True)
            .distinct()
        )
        self.fields["vendor_circuit_id"].choices += [
            (value, value) for value in vendor_circuit_ids
        ]

        # Update vendor choices dynamically
        vendors = (
            OpticalSpan.objects.order_by("vendor")
            .values_list("vendor", flat=True)
            .distinct()
        )
        self.fields["vendor"].choices += [(value, value) for value in vendors]


class OpticalSpanImportForm(NetBoxModelImportForm):
    grid = CSVModelChoiceField(queryset=OpticalGrid.objects.all(), required=True)
    mux_a = CSVModelChoiceField(queryset=Device.objects.all(), required=False)
    mux_z = CSVModelChoiceField(queryset=Device.objects.all(), required=False)

    class Meta:
        model = OpticalSpan
        fields = [
            "name",
            "site_a",
            "site_b",
            "grid",
            "mux_a",
            "mux_z",
            "vendor_circuit_id",
            "vendor",
            "description",
        ]


class OpticalConnectionForm(NetBoxModelForm):
    span = DynamicModelChoiceField(
        queryset=OpticalSpan.objects.all(),
        required=True,
        label="Optical Span",
        widget=APISelect(api_url="/api/plugins/optics/optical-spans/"),
        help_text="Select the optical span. Note: When changing span, you need to re-select wavelength and interfaces to ensure they belong to this span.",
    )  # todo reset interafes and wavelength when span changes
    device_a = DynamicModelChoiceField(
        queryset=Device.objects.all(),
        required=False,
        label="Device A",
        help_text="Optional: Filter interfaces by device",
    )
    device_z = DynamicModelChoiceField(
        queryset=Device.objects.all(),
        required=False,
        label="Device Z",
        help_text="Optional: Filter interfaces by device",
    )
    interface_a = DynamicModelChoiceField(
        queryset=Interface.objects.all(),
        required=True,
        label="Interface A",
        # todo only physical interfaces
        query_params={"device_id": "$device_a"},
    )
    interface_z = DynamicModelChoiceField(
        queryset=Interface.objects.all(),
        required=True,
        label="Interface Z",
        query_params={"device_id": "$device_z"},
    )
    wavelength = DynamicModelChoiceField(
        queryset=OpticalGridWavelength.objects.all(),
        required=True,
        label="Wavelength",
        widget=APISelect(api_url="/api/plugins/optics/optical-grid-wavelengths/"),
        query_params={"span": "$span"},
        help_text="Wavelength from the span's grid",
    )

    class Meta:
        model = OpticalConnection
        fields = [
            "name",
            "span",
            "device_a",
            "interface_a",
            "device_z",
            "interface_z",
            "wavelength",
            "tx_power",
            "description",
        ]
        help_texts = {
            "wavelength": "Wavelength from the span's grid. Must be available and not "
            "already used by another connection."
        }


class OpticalConnectionFilterForm(NetBoxModelFilterSetForm):
    """Form for filtering OpticalConnection instances."""

    model = OpticalConnection
    q = forms.CharField(required=False, label="Search")
    span_id = DynamicModelMultipleChoiceField(
        queryset=OpticalSpan.objects.all(),
        required=False,
        label="Optical Span",
        widget=APISelectMultiple(api_url="/api/plugins/optics/optical-spans/"),
    )
    site_a_id = DynamicModelMultipleChoiceField(
        queryset=Site.objects.all(),
        required=False,
        label="Site A",
    )
    site_b_id = DynamicModelMultipleChoiceField(
        queryset=Site.objects.all(),
        required=False,
        label="Site B",
    )
    device_id = DynamicModelMultipleChoiceField(
        queryset=Device.objects.all(),
        required=False,
        label="Device",
    )
    interface_id = DynamicModelMultipleChoiceField(
        queryset=Interface.objects.all(),
        required=False,
        label="Interface",
        query_params={"device_id": "$device_id"},
    )
    wavelength = forms.ChoiceField(
        choices=[("", "Select Wavelength")],  # Empty choices initially
        required=False,
        label="Wavelength",
    )
    vendor_circuit_id = forms.ChoiceField(
        choices=[("", "Select Vendor Circuit ID")],  # Empty choices initially
        required=False,
        label="Vendor Circuit ID",
    )
    tx_power = forms.DecimalField(required=False, label="Transmit Power")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Update vendor_circuit_id choices dynamically
        vendor_circuit_ids = (
            OpticalSpan.objects.order_by("vendor_circuit_id")
            .values_list("vendor_circuit_id", flat=True)
            .distinct()
        )
        self.fields["vendor_circuit_id"].choices += [
            (value, value) for value in vendor_circuit_ids if value
        ]
        
        # Update wavelength choices dynamically from all wavelengths
        wavelengths = (
            OpticalGridWavelength.objects.order_by("value")
            .values_list("value", flat=True)
            .distinct()
        )
        self.fields["wavelength"].choices += [
            (str(w), str(w)) for w in wavelengths
        ]


class OpticalConnectionImportForm(NetBoxModelImportForm):
    span = CSVModelChoiceField(queryset=OpticalSpan.objects.all(), required=True)
    wavelength = CSVModelChoiceField(
        queryset=OpticalGridWavelength.objects.all(), required=True
    )

    class Meta:
        model = OpticalConnection
        fields = [
            "name",
            "span",
            "interface_a",
            "interface_z",
            "wavelength",
            "tx_power",
            "description",
        ]


class MuxWavelengthMapForm(NetBoxModelForm):
    mux = DynamicModelChoiceField(
        queryset=Device.objects.all(),
        required=True,
        label="Mux Device",
        query_params={"role": MUX_ROLE_SLUG},
        help_text="Device with role=mux",
    )
    port = DynamicModelChoiceField(
        queryset=Interface.objects.all(),
        required=True,
        label="Port",
        query_params={"device_id": "$mux"},
        help_text="Port interface on the mux",
    )
    wavelength = DynamicModelChoiceField(
        queryset=OpticalGridWavelength.objects.all(),
        required=True,
        label="Wavelength",
        help_text="Wavelength assigned to this port",
        widget=APISelect(api_url="/api/plugins/optics/optical-grid-wavelengths/"),
    )

    class Meta:
        model = MuxWavelengthMap
        fields = ["mux", "port", "wavelength"]


class MuxWavelengthMapFilterForm(NetBoxModelFilterSetForm):
    """Form for filtering MuxWavelengthMap instances."""

    model = MuxWavelengthMap
    q = forms.CharField(required=False, label="Search")
    mux = DynamicModelMultipleChoiceField(
        queryset=Device.objects.all(),
        required=False,
        label="Mux Device",
        query_params={"role": MUX_ROLE_SLUG},
    )
    wavelength = DynamicModelMultipleChoiceField(
        queryset=OpticalGridWavelength.objects.all(),
        required=False,
        label="Wavelength",
        widget=APISelectMultiple(
            api_url="/api/plugins/optics/optical-grid-wavelengths/"
        ),
    )
    span = DynamicModelMultipleChoiceField(
        queryset=OpticalSpan.objects.all(),
        required=False,
        label="Span",
        widget=APISelectMultiple(api_url="/api/plugins/optics/optical-spans/"),
    )


class MuxWavelengthMapImportForm(NetBoxModelImportForm):
    mux = CSVModelChoiceField(queryset=Device.objects.all(), required=True)
    port = CSVModelChoiceField(queryset=Interface.objects.all(), required=True)
    wavelength = CSVModelChoiceField(
        queryset=OpticalGridWavelength.objects.all(), required=True
    )

    class Meta:
        model = MuxWavelengthMap
        fields = ["mux", "port", "wavelength"]

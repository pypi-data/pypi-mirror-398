from decimal import Decimal

from dcim.models import Device, Interface, Site
from django.core.exceptions import ValidationError
from django.core.validators import (
    DecimalValidator,
    MaxValueValidator,
    MinValueValidator,
    RegexValidator,
)
from django.db import models
from django.urls import reverse
from netbox.models import PrimaryModel as NetBoxModel
from utilities.querysets import RestrictedQuerySet

from .choices import WavelengthStatus
from .constants import MUX_ROLE_SLUG, NAMESPACE


# todo mb add labels to models, check is lablel already included to netbox base model
class OpticalGridType(NetBoxModel):
    """Optical grid type template

    Note that modifying grid type object does not affect existing spans
    """

    objects = RestrictedQuerySet.as_manager()

    name = models.CharField(
        max_length=100,
        help_text="Name of the grid type (e.g. DWDM 50GHz, CWDM, Offset N)",
        default="",
        blank=True,
    )
    spacing = models.IntegerField(
        help_text="Wavelength spacing in GHz.",
        validators=[MinValueValidator(1)],
    )
    description = models.TextField(blank=True, help_text="Description of the grid.")

    csv_headers = ["name", "spacing", "allowed_wavelengths", "description"]

    def get_absolute_url(self):
        """Overridden to add plugins namespace"""
        return reverse(f"plugins:{NAMESPACE}:opticalgridtype", args=[self.pk])

    def __str__(self):
        return f"OpticalGrid {self.name} {self.spacing} GHz"

    def to_csv(self):
        """Convert model to CSV for legacy export"""
        wavelengths = [str(wl.value) for wl in self.allowed_wavelengths.all()]
        return (
            self.name,
            self.spacing,
            ",".join(wavelengths),
            self.description,
        )

    class Meta:
        ordering = ["spacing"]
        verbose_name = "Optical Grid Type"
        verbose_name_plural = "Optical Grid Types"


class OpticalGridTypeWavelength(NetBoxModel):
    """Individual wavelength in an optical grid type template"""

    objects = RestrictedQuerySet.as_manager()

    grid_type = models.ForeignKey(
        OpticalGridType,
        on_delete=models.CASCADE,
        related_name="allowed_wavelengths",
        help_text="Grid type this wavelength belongs to",
    )
    value = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[
            DecimalValidator(max_digits=6, decimal_places=2),
            MinValueValidator(Decimal("0.01")),
        ],
        help_text="Wavelength value in nm",
    )

    def clean(self):
        super().clean()

        # Disallow changing grid_type after creation
        if self.pk:  # Object already exists
            try:
                original = OpticalGridTypeWavelength.objects.get(pk=self.pk)
                if original.grid_type != self.grid_type:
                    raise ValidationError(
                        {"grid_type": "grid_type cannot be changed after creation."}
                    )
            except OpticalGridTypeWavelength.DoesNotExist:
                pass  # New object, no validation needed

    def get_absolute_url(self):
        return reverse(f"plugins:{NAMESPACE}:opticalgridtypewavelength", args=[self.pk])

    def __str__(self):
        return f"{self.value} nm"

    class Meta:
        ordering = ["value"]
        unique_together = [["grid_type", "value"]]
        verbose_name = "Grid Type Wavelength"
        verbose_name_plural = "Grid Type Wavelengths"


class OpticalGrid(NetBoxModel):
    """Optical grid instance"""

    objects = RestrictedQuerySet.as_manager()

    name = models.CharField(
        max_length=100,
        help_text="Name of the grid instance",
        default="",
        blank=True,
    )

    grid_type = models.ForeignKey(
        OpticalGridType,
        on_delete=models.PROTECT,
        related_name="grids",
        help_text="Grid type template this instance is based on",
    )

    spacing = models.IntegerField(
        blank=True,
        help_text="Wavelength spacing in GHz (copied from template).",
        validators=[MinValueValidator(1)],
    )

    description = models.TextField(blank=True, help_text="Description of the grid.")

    csv_headers = [
        "name",
        "grid_type",
        "spacing",
        "description",
    ]

    def clean(self):
        super().clean()

        # Disallow changing grid_type after creation
        if self.pk:  # Object already exists
            try:
                original = OpticalGrid.objects.get(pk=self.pk)
                if original.grid_type != self.grid_type:
                    raise ValidationError(
                        {"grid_type": "grid_type cannot be changed after creation."}
                    )
            except OpticalGrid.DoesNotExist:
                pass  # New object, no validation needed

    def save(self, *args, **kwargs):
        is_new = not self.pk

        if is_new:
            # populate from template
            self.spacing = self.grid_type.spacing
            if not self.name:
                self.name = self.grid_type.name
            if not self.description:
                self.description = self.grid_type.description

        super().save(*args, **kwargs)

        # Create wavelength objects from template if this is a new grid
        if is_new:
            for template_wavelength in self.grid_type.allowed_wavelengths.all():
                OpticalGridWavelength.objects.create(
                    grid=self, value=template_wavelength.value
                )

    def get_absolute_url(self):
        return reverse(f"plugins:{NAMESPACE}:opticalgrid", args=[self.pk])

    def __str__(self):
        return f"OpticalGrid {self.id}: {self.name or self.spacing}"

    class Meta:
        ordering = ["name"]
        verbose_name = "Optical Grid"
        verbose_name_plural = "Optical Grids"


class OpticalGridWavelength(NetBoxModel):
    """Individual wavelength in an optical grid instance"""

    objects = RestrictedQuerySet.as_manager()

    grid = models.ForeignKey(
        OpticalGrid,
        on_delete=models.CASCADE,
        related_name="allowed_wavelengths",
        help_text="Optical grid this wavelength belongs to",
    )
    value = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[
            DecimalValidator(max_digits=6, decimal_places=2),
            MinValueValidator(Decimal("0.01")),
        ],
        help_text="Wavelength value in nm",
    )

    def clean(self):
        super().clean()

        # Disallow changing grid_id after creation
        if self.pk:  # Object already exists
            try:
                original = OpticalGridWavelength.objects.get(pk=self.pk)
                if original.grid_id != self.grid_id:
                    raise ValidationError(
                        {
                            "grid": "Cannot change grid after creation. Create a new wavelength instead."
                        }
                    )
            except OpticalGridWavelength.DoesNotExist:
                pass  # New object, no validation needed

    def get_absolute_url(self):
        return reverse(f"plugins:{NAMESPACE}:opticalgridwavelength", args=[self.pk])

    def __str__(self):
        return f"{self.value} nm"

    class Meta:
        ordering = ["value"]
        unique_together = [["grid", "value"]]
        verbose_name = "Grid Wavelength"
        verbose_name_plural = "Grid Wavelengths"


class OpticalSpan(NetBoxModel):
    objects = RestrictedQuerySet.as_manager()

    name = models.CharField(
        max_length=100,
        help_text="Name of the connection",
        default="",
        blank=True,
    )
    site_a = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        related_name="optical_spans_as_a",  # todo use optical_spans for both
    )
    site_b = models.ForeignKey(
        Site, on_delete=models.CASCADE, related_name="optical_spans_as_b"
    )
    grid = models.ForeignKey(
        OpticalGrid,
        on_delete=models.PROTECT,
        related_name="spans",
        help_text="Optical grid defining wavelengths for this span.",
    )

    description = models.TextField(blank=True, help_text="Description of the span.")

    vendor_circuit_id = models.CharField(
        max_length=100,
        unique=True,
        # todo find and use actual format
        validators=[RegexValidator(regex=r"^\S+$", message="No spaces allowed.")],
        help_text="Unique identifier for the circuit.",
    )
    vendor = models.CharField(max_length=100, help_text="Vendor name.")

    mux_a = models.ForeignKey(
        Device,
        on_delete=models.PROTECT,
        related_name="optical_spans_as_mux_a",
        blank=True,
        null=True,
        help_text="Mux device at site A (Device with role=mux)",
    )
    mux_z = models.ForeignKey(
        Device,
        on_delete=models.PROTECT,
        related_name="optical_spans_as_mux_z",
        blank=True,
        null=True,
        help_text="Mux device at site Z (Device with role=mux)",
    )

    csv_headers = [
        "name",
        "site_a",
        "site_b",
        "grid",
        "description",
        "vendor_circuit_id",
        "vendor",
        "mux_a",
        "mux_z",
    ]

    @property
    def allowed_wavelengths(self):
        """Get wavelengths from grid"""
        return self.grid.allowed_wavelengths

    def clean(self):
        super().clean()

        # Skip validation if required fields are not set (check ID fields to avoid RelatedObjectDoesNotExist)
        if not self.site_a_id or not self.site_b_id or not self.grid_id:
            return

        # todo code cleanup
        # Validate mux devices if provided
        if self.mux_a:
            if (
                not hasattr(self.mux_a, "device_role")
                or self.mux_a.device_role.slug != MUX_ROLE_SLUG
            ):
                raise ValidationError(
                    {"mux_a": f"Device must have role '{MUX_ROLE_SLUG}'"}
                )

            if self.mux_a.site != self.site_a:
                raise ValidationError({"mux_a": "Mux device must be at site A"})

            # Check if mux_a is already used in another span
            existing_span = (
                OpticalSpan.objects.filter(
                    models.Q(mux_a=self.mux_a) | models.Q(mux_z=self.mux_a)
                )
                .exclude(pk=self.pk)
                .first()
            )
            if existing_span:
                raise ValidationError(
                    {
                        "mux_a": f"Mux device is already used in span '{existing_span.vendor_circuit_id}'"
                    }
                )

            # Validate that mux_a grid matches the span's grid
            mux_a_grids = self.mux_a.mux_maps.values_list(
                "wavelength__grid", flat=True
            ).distinct()
            if mux_a_grids and self.grid.id not in mux_a_grids:
                raise ValidationError(
                    {
                        "mux_a": "Selected mux device already has port mapping configured with grid not matching this span's grid"
                    }
                )

        if self.mux_z:
            if (
                not hasattr(self.mux_z, "device_role")
                or self.mux_z.device_role.slug != MUX_ROLE_SLUG
            ):
                raise ValidationError(
                    {"mux_z": f"Device must have role '{MUX_ROLE_SLUG}'"}
                )

            if self.mux_z.site != self.site_b:
                raise ValidationError({"mux_z": "Mux device must be at site Z"})

            # Check if mux_z is already used in another span
            existing_span = (
                OpticalSpan.objects.filter(
                    models.Q(mux_a=self.mux_z) | models.Q(mux_z=self.mux_z)
                )
                .exclude(pk=self.pk)
                .first()
            )
            if existing_span:
                raise ValidationError(
                    {
                        "mux_z": f"Mux device is already used in span '{existing_span.vendor_circuit_id}'"
                    }
                )

            # Validate that mux_z grid matches the span's grid
            mux_z_grids = self.mux_z.mux_maps.values_list(
                "wavelength__grid", flat=True
            ).distinct()
            if mux_z_grids and self.grid.id not in mux_z_grids:
                raise ValidationError(
                    {
                        "mux_z": "Selected mux device already has port mapping configured with grid not matching this span's grid"
                    }
                )

        # Disallow changing grid after creation
        if self.pk:  # Object already exists
            try:
                original = OpticalSpan.objects.get(pk=self.pk)
                if original.grid != self.grid:
                    raise ValidationError(
                        {"grid": "grid cannot be changed after creation."}
                    )
            except OpticalSpan.DoesNotExist:
                pass  # New object, no validation needed

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def get_wavelength_statuses(self, status_filter=None):
        """Returns a list of wavelengths with their usage status and connection_id, filtered by status if specified"""

        used_wavelengths = OpticalConnection.objects.filter(span=self).values(
            "wavelength_id", "id"
        )

        wavelength_to_connection = {
            item["wavelength_id"]: item["id"] for item in used_wavelengths
        }

        # Build the output list using grid wavelengths
        wavelengths = [
            {
                "wavelength": wl.value,
                "wavelength_id": wl.id,
                "status": (
                    WavelengthStatus.RESERVED
                    if wl.id in wavelength_to_connection
                    else WavelengthStatus.FREE
                ),
                "connection_id": wavelength_to_connection.get(
                    wl.id
                ),  # None if not used
            }
            for wl in self.grid.allowed_wavelengths.all()
        ]

        if status_filter is None:
            return wavelengths

        return [w for w in wavelengths if w["status"] == status_filter]

    def get_absolute_url(self):
        return reverse(f"plugins:{NAMESPACE}:opticalspan", args=[self.pk])

    def __str__(self):
        return f"OpticalSpan {self.id} (Circuit: {self.vendor_circuit_id})"

    def to_csv(self):
        """Convert model to CSV for legacy export"""
        return (
            self.name,
            self.site_a.name,
            self.site_b.name,
            self.grid.name if self.grid else None,
            self.description,
            self.vendor_circuit_id,
            self.vendor,
            self.mux_a.name if self.mux_a else None,
            self.mux_z.name if self.mux_z else None,
        )

    class Meta:
        ordering = ["vendor_circuit_id"]
        verbose_name = "Optical Span"
        verbose_name_plural = "Optical Spans"


class OpticalConnection(NetBoxModel):
    objects = RestrictedQuerySet.as_manager()

    name = models.CharField(
        max_length=100,
        help_text="Name of the entity.",
        default="",
        blank=True,
    )
    span = models.ForeignKey(
        OpticalSpan, on_delete=models.CASCADE, related_name="connections"
    )
    wavelength = models.ForeignKey(
        OpticalGridWavelength,
        on_delete=models.PROTECT,
        related_name="connections",
        help_text="Wavelength from the span's grid",
    )
    tx_power = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        validators=[MaxValueValidator(127)],
        verbose_name="transmit power (dBm)",
    )
    interface_a = models.ForeignKey(
        Interface, on_delete=models.CASCADE, related_name="connections_as_a"
    )
    interface_z = models.ForeignKey(
        Interface, on_delete=models.CASCADE, related_name="connections_as_z"
    )

    description = models.TextField(
        blank=True, help_text="Description of the Connection."
    )

    csv_headers = [
        "name",
        "span",
        "wavelength",
        "tx_power",
        "interface_a",
        "interface_z",
        "description",
    ]

    def clean(self):
        super().clean()

        self._validate_wavelength()
        self._validate_interfaces()

    def _validate_wavelength(self):
        """Validate wavelength against span's grid and availability."""
        # Skip validation if wavelength or span is not set (check ID fields to avoid RelatedObjectDoesNotExist)
        if not self.wavelength_id or not self.span_id:
            return
            
        # Check if wavelength belongs to the span's grid
        if self.wavelength.grid != self.span.grid:
            raise ValidationError(
                {
                    "wavelength": f"Wavelength {self.wavelength.value} does not belong to this span's grid"
                },
            )

        # Check if wavelength is already used by another connection on this span
        existing_connection = self.span.connections.filter(wavelength=self.wavelength)
        if self.pk:
            existing_connection = existing_connection.exclude(pk=self.pk)

        if existing_connection.exists():
            raise ValidationError(
                {
                    "wavelength": f"Wavelength {self.wavelength.value} is already reserved by another connection"
                },
            )

    def _validate_interfaces(self):
        # Skip validation if interfaces are not set (check ID fields to avoid RelatedObjectDoesNotExist)
        if not self.interface_a_id or not self.interface_z_id:
            return
            
        # Check that interfaces are different
        if self.interface_a == self.interface_z:
            raise ValidationError(
                {
                    "interface_a": "Interface A must be different from Interface Z",
                    "interface_z": "Interface Z must be different from Interface A",
                },
            )

        # check that device belong to those sites
        device_a = self.interface_a.device
        device_z = self.interface_z.device

        # Prevent mux devices from being used in connections
        if (
            hasattr(device_a, "device_role")
            and device_a.device_role.slug == MUX_ROLE_SLUG
        ):
            raise ValidationError(
                {
                    "interface_a": f"Mux devices cannot be used directly in connections. Device {device_a} has role '{MUX_ROLE_SLUG}'"
                },
                code="invalid_mux_device_a",
            )

        if (
            hasattr(device_z, "device_role")
            and device_z.device_role.slug == MUX_ROLE_SLUG
        ):
            raise ValidationError(
                {
                    "interface_z": f"Mux devices cannot be used directly in connections. Device {device_z} has role '{MUX_ROLE_SLUG}'"
                },
                code="invalid_mux_device_z",
            )

        if not (device_a.site == self.span.site_a or device_a.site == self.span.site_b):
            raise ValidationError(
                {
                    "interface_a": f"Device {device_a} {self.interface_a} is not part of the span {self.span}"
                },
                code="invalid_interface_a",
            )

        if not (device_z.site == self.span.site_a or device_z.site == self.span.site_b):
            raise ValidationError(
                {
                    "interface_z": f"Device {device_z} {self.interface_z} is not part of the span {self.span}"
                },
                code="invalid_interface_z",
            )

    def get_absolute_url(self):
        return reverse(f"plugins:{NAMESPACE}:opticalconnection", args=[self.pk])

    def __str__(self):
        return f"OpticalConnection {self.id} {self.name}"

    def to_csv(self):
        """Convert model to CSV for legacy export"""
        return (
            self.name,
            self.span.name,
            self.wavelength.value,
            self.tx_power,
            f"{self.interface_a.device.name}:{self.interface_a.name}",
            f"{self.interface_z.device.name}:{self.interface_z.name}",
            self.description,
        )

    class Meta:
        verbose_name = "Optical Connection"
        verbose_name_plural = "Optical Connections"
        constraints = [
            models.UniqueConstraint(
                fields=["interface_a"],
                name="unique_interface_a",
            ),
            models.UniqueConstraint(
                fields=["interface_z"],
                name="unique_interface_z",
            ),
            models.UniqueConstraint(
                fields=["wavelength", "span"],
                name="unique_wavelength_per_span",
            ),
            models.CheckConstraint(
                check=~models.Q(interface_a=models.F("interface_z")),
                name="interface_a_not_equal_interface_z",
            ),
        ]


class MuxWavelengthMap(NetBoxModel):
    """Per-instance mapping of mux port ↔ wavelength"""

    objects = RestrictedQuerySet.as_manager()

    mux = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name="mux_maps",
        help_text="Mux device (Device with role=mux)",
    )
    port = models.ForeignKey(
        Interface, on_delete=models.CASCADE, help_text="Port interface on the mux"
    )
    wavelength = models.ForeignKey(
        OpticalGridWavelength,
        on_delete=models.PROTECT,
        help_text="Wavelength assigned to this port",
    )

    csv_headers = ["mux", "port", "wavelength", "grid"]

    def clean(self):
        super().clean()

        # Skip validation if required fields are not set (check ID fields to avoid RelatedObjectDoesNotExist)
        if not self.mux_id or not self.port_id or not self.wavelength_id:
            return

        # Validate that mux has role=mux
        if (
            not hasattr(self.mux, "device_role")
            or self.mux.device_role.slug != MUX_ROLE_SLUG
        ):
            raise ValidationError(f"Device must have role '{MUX_ROLE_SLUG}'")

        # Validate that port belongs to the mux device
        if self.port.device.id != self.mux.id:
            raise ValidationError(
                f"Port must belong to the mux device. Port device ID: {self.port.device.id}, "
                "Mux device ID: {self.mux.id}"
            )

        # Enforce that a mux has mappings from a single grid only
        existing_grid_ids = list(
            MuxWavelengthMap.objects.filter(mux=self.mux)
            .exclude(pk=self.pk)
            .values_list("wavelength__grid_id", flat=True)
            .distinct()
        )
        existing_grid_ids_set = set(existing_grid_ids)
        if len(existing_grid_ids_set) > 1:
            # Data is already inconsistent; surface a clear validation error
            existing_grid_names = list(
                OpticalGrid.objects.filter(id__in=existing_grid_ids_set).values_list(
                    "name", flat=True
                )
            )
            raise ValidationError(
                "Mux device already has mappings from multiple grids, which is invalid: "
                f"{', '.join(existing_grid_names)}. "
                "Please reconcile existing mappings to a single grid."
            )
        elif len(existing_grid_ids_set) == 1:
            # Enforce same grid as existing mappings
            [only_grid_id] = list(existing_grid_ids_set)
            if self.wavelength.grid_id != only_grid_id:
                only_grid_name = OpticalGrid.objects.get(id=only_grid_id).name
                raise ValidationError(
                    "All wavelength mappings for a mux must use a single grid. "
                    f"Existing grid: {only_grid_name}; selected wavelength uses grid "
                    f"'{self.wavelength.grid.name}'."
                )

        # If mux is assigned to a span, ensure the grid also matches the span's grid
        # Note: span assignment is not required for creating mux wavelength maps.
        # If a span exists, we do not enforce its grid here; enforcement is handled at span/connection level.

    def get_absolute_url(self):
        return reverse(f"plugins:{NAMESPACE}:muxwavelengthmap", args=[self.pk])

    def to_csv(self):
        """Convert model to CSV for legacy export"""
        return (
            self.mux.name,
            self.port.name,
            self.wavelength.value,
            self.wavelength.grid.name,
        )

    def __str__(self):
        return f"{self.mux.id}:{self.port.id} → {self.wavelength.id}"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["mux", "port"], name="unique_mux_port"),
            models.UniqueConstraint(
                fields=["mux", "wavelength"], name="unique_mux_wavelength"
            ),
        ]
        verbose_name = "Mux Wavelength Map"
        verbose_name_plural = "Mux Wavelength Maps"

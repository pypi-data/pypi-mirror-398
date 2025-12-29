from rest_framework import serializers

from dcim.api.nested_serializers import (
    NestedInterfaceSerializer,
    NestedSiteSerializer,
    NestedDeviceSerializer,
)
from netbox.api.serializers import NetBoxModelSerializer, WritableNestedSerializer


from ..models import (
    OpticalGridType,
    OpticalGrid,
    OpticalGridWavelength,
    OpticalGridTypeWavelength,
    OpticalSpan,
    OpticalConnection,
    MuxWavelengthMap,
)
from ..choices import WavelengthStatus

# todo preload related objects


class NestedOpticalGridWavelengthSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netbox_optics-api:opticalgridwavelength-detail"
    )
    value = serializers.DecimalField(
        max_digits=6, decimal_places=2, coerce_to_string=False
    )

    class Meta:
        model = OpticalGridWavelength
        fields = ["id", "url", "display", "value"]


class NestedOpticalGridTypeWavelengthSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netbox_optics-api:opticalgridtypewavelength-detail"
    )
    value = serializers.DecimalField(
        max_digits=6, decimal_places=2, coerce_to_string=False
    )

    class Meta:
        model = OpticalGridTypeWavelength
        fields = ["id", "url", "display", "value"]


class NestedOpticalConnectionSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netbox_optics-api:opticalconnection-detail"
    )

    class Meta:
        model = OpticalConnection
        fields = ["id", "url", "display", "name"]


class NestedMuxWavelengthMapSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netbox_optics-api:muxwavelengthmap-detail"
    )

    class Meta:
        model = MuxWavelengthMap
        fields = ["id", "url", "display", "mux", "port", "wavelength"]


class NestedOpticalGridTypeSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netbox_optics-api:opticalgridtype-detail"
    )

    class Meta:
        model = OpticalGridType
        fields = ["id", "url", "display", "name"]


class OpticalGridTypeWavelengthSerializer(NetBoxModelSerializer):
    grid_type = NestedOpticalGridTypeSerializer(
        required=True, help_text="Grid type this wavelength belongs to"
    )
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netbox_optics-api:opticalgridtypewavelength-detail"
    )
    value = serializers.DecimalField(
        max_digits=6, decimal_places=2, coerce_to_string=False
    )

    class Meta:
        model = OpticalGridTypeWavelength
        fields = [
            "id",
            "url",
            "display",
            "value",
            "grid_type",
            "created",
            "last_updated",
        ]
        brief_fields = ["id", "url", "display", "value", "grid_type"]


class OpticalGridTypeSerializer(NetBoxModelSerializer):
    name = serializers.CharField(required=False, allow_blank=True)
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netbox_optics-api:opticalgridtype-detail"
    )
    allowed_wavelengths = NestedOpticalGridTypeWavelengthSerializer(
        many=True, read_only=True, help_text="Wavelengths available in this grid type"
    )

    class Meta:
        model = OpticalGridType
        fields = "__all__"
        brief_fields = ["id", "url", "display", "name"]


class NestedOpticalGridSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netbox_optics-api:opticalgrid-detail"
    )

    class Meta:
        model = OpticalGrid
        fields = ["id", "url", "display", "name"]


class OpticalGridWavelengthSerializer(NetBoxModelSerializer):
    grid = NestedOpticalGridSerializer(
        required=True, help_text="Optical grid this wavelength belongs to"
    )
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netbox_optics-api:opticalgridwavelength-detail"
    )
    value = serializers.DecimalField(
        max_digits=6, decimal_places=2, coerce_to_string=False
    )

    class Meta:
        model = OpticalGridWavelength
        fields = [
            "id",
            "url",
            "display",
            "value",
            "grid",
            "created",
            "last_updated",
        ]
        brief_fields = ["id", "url", "display", "value", "grid"]


class OpticalGridSerializer(NetBoxModelSerializer):
    name = serializers.CharField(required=False, allow_blank=True)
    grid_type = NestedOpticalGridTypeSerializer(
        required=True, help_text="Grid type template this instance is based on"
    )
    spacing = serializers.IntegerField(
        required=False,
        allow_null=False,
        min_value=1,
        help_text="Wavelength spacing in GHz (copied from template)",
    )
    allowed_wavelengths = NestedOpticalGridWavelengthSerializer(
        many=True, read_only=True, help_text="Wavelengths available in this grid"
    )
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netbox_optics-api:opticalgrid-detail"
    )

    class Meta:
        model = OpticalGrid
        fields = "__all__"
        brief_fields = ["id", "url", "display", "name"]

    def create(self, validated_data):
        # If spacing is not provided, populate it from grid_type
        spacing = validated_data.get("spacing")
        grid_type = validated_data.get("grid_type")

        if not spacing and grid_type:
            validated_data["spacing"] = grid_type.spacing

        return super().create(validated_data)


class NestedOpticalSpanSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netbox_optics-api:opticalspan-detail"
    )

    class Meta:
        model = OpticalSpan
        fields = ["id", "url", "display", "name"]


class OpticalSpanSerializer(NetBoxModelSerializer):
    name = serializers.CharField(required=False, allow_blank=True)
    site_a = NestedSiteSerializer(
        many=False,
        read_only=False,
        required=True,
        help_text="Connected Site A side",
    )
    site_b = NestedSiteSerializer(
        many=False,
        read_only=False,
        required=True,
        help_text="Connected Site B side",
    )
    grid = NestedOpticalGridSerializer(
        required=True, help_text="Optical grid defining wavelengths for this span"
    )
    mux_a = NestedDeviceSerializer(
        many=False,
        read_only=False,
        required=False,
        allow_null=True,
        help_text="Mux device at site A (Device with role=mux)",
    )
    mux_z = NestedDeviceSerializer(
        many=False,
        read_only=False,
        required=False,
        allow_null=True,
        help_text="Mux device at site Z (Device with role=mux)",
    )
    wavelengths = serializers.SerializerMethodField(read_only=True)
    connections = NestedOpticalConnectionSerializer(
        many=True, read_only=True, help_text="Connections on this span"
    )
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netbox_optics-api:opticalspan-detail"
    )

    class Meta:
        model = OpticalSpan
        fields = [
            "id",
            "url",
            "display",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
            "name",
            "site_a",
            "site_b",
            "grid",
            "description",
            "vendor_circuit_id",
            "vendor",
            "mux_a",
            "mux_z",
            "wavelengths",
            "connections",
        ]
        read_only_fields = ["wavelengths", "connections"]
        brief_fields = [
            "id",
            "url",
            "display",
            "name",
            "vendor_circuit_id",
        ]

    def get_wavelengths(self, obj):
        wavelengths = obj.get_wavelength_statuses()
        return WavelengthSerializer(wavelengths, many=True).data


class OpticalConnectionSerializer(NetBoxModelSerializer):
    name = serializers.CharField(required=False, allow_blank=True)
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netbox_optics-api:opticalconnection-detail"
    )
    interface_a = NestedInterfaceSerializer(
        many=False,
        read_only=False,
        required=True,
        help_text="Connected Interface A side",
    )
    interface_z = NestedInterfaceSerializer(
        many=False,
        read_only=False,
        required=True,
        help_text="Connected Interface Z side",
    )
    span = NestedOpticalSpanSerializer()
    wavelength = NestedOpticalGridWavelengthSerializer(
        required=True, help_text="Wavelength from the span's grid"
    )

    class Meta:
        model = OpticalConnection
        fields = "__all__"
        brief_fields = [
            "id",
            "url",
            "display",
            "name",
            "span",
            "wavelength",
            "interface_a",
            "interface_z",
        ]


class WavelengthSerializer(serializers.Serializer):
    wavelength = serializers.DecimalField(
        max_digits=6, decimal_places=2, coerce_to_string=False
    )
    wavelength_id = serializers.IntegerField()
    status = serializers.ChoiceField(choices=WavelengthStatus.choices())
    connection_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        brief_fields = ["wavelength", "wavelength_id", "status", "connection_id"]


class MuxWavelengthMapSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netbox_optics-api:muxwavelengthmap-detail"
    )
    mux = NestedDeviceSerializer(
        required=True, help_text="Mux device (Device with role=mux)"
    )
    port = NestedInterfaceSerializer(
        required=True, help_text="Port interface on the mux"
    )
    wavelength = NestedOpticalGridWavelengthSerializer(
        required=True, help_text="Wavelength assigned to this port"
    )

    class Meta:
        model = MuxWavelengthMap
        fields = "__all__"
        brief_fields = ["id", "url", "display", "mux", "port", "wavelength"]

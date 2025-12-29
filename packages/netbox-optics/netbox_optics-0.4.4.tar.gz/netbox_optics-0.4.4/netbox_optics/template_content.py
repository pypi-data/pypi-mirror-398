from django.db import models
from netbox.plugins import PluginTemplateExtension

from .models import OpticalConnection, MuxWavelengthMap, OpticalSpan
from .constants import MUX_ROLE_SLUG


class DeviceOpticalConnections(PluginTemplateExtension):
    """Inject optical connections content into device pages"""

    model = "dcim.device"

    def full_width_page(self):
        """Display optical connections panel on device pages"""
        device = self.context["object"]
        if (
            hasattr(device, "device_role")
            and device.device_role
            and device.device_role.slug == MUX_ROLE_SLUG
        ):
            return ""

        base_filter = models.Q(interface_a__device=device) | models.Q(
            interface_z__device=device
        )
        if not OpticalConnection.objects.filter(base_filter).exists():
            return ""

        # Single optimized query: fetch all connections with related objects
        connections = list(
            OpticalConnection.objects.filter(base_filter).select_related(
                "interface_a",
                "interface_a__device",
                "interface_z",
                "interface_z__device",
                "span",
                "wavelength",
            )
        )

        if not connections:
            return ""

        return self.render(
            "netbox_optics/inc/device_optical_connections.html",
            {
                "device": device,
                "connections": connections,
            },
        )


class InterfaceOpticalConnection(PluginTemplateExtension):
    """Show optical connection and mux mapping details on interface pages"""

    model = "dcim.interface"

    def right_page(self):
        """Display optical connection and mux mapping info on interface detail page"""
        interface = self.context["object"]

        has_mux_mapping = MuxWavelengthMap.objects.filter(port=interface).exists()
        has_connections = OpticalConnection.objects.filter(
            models.Q(interface_a=interface) | models.Q(interface_z=interface)
        ).exists()

        if not has_mux_mapping and not has_connections:
            return ""

        connection = OpticalConnection.objects.filter(
            models.Q(interface_a=interface) | models.Q(interface_z=interface)
        ).first()

        mux_mapping = MuxWavelengthMap.objects.filter(port=interface).select_related(
            "mux", "wavelength", "wavelength__grid"
        ).first()

        # If this is a mux port, try to find the span that references this mux device
        mux_span = None
        if mux_mapping:
            try:
                mux_span = OpticalSpan.objects.get(
                    models.Q(mux_a=interface.device) | models.Q(mux_z=interface.device)
                )
            except OpticalSpan.DoesNotExist:
                mux_span = None

        return self.render(
            "netbox_optics/inc/interface_optical_connection.html",
            {
                "interface": interface,
                "connection": connection,
                "mux_mapping": mux_mapping,
                "mux_span": mux_span,
            },
        )


class DeviceMuxPortMapTable(PluginTemplateExtension):
    """Inject Mux Port Map table into mux device pages"""

    model = "dcim.device"

    def full_width_page(self):
        """Display Mux Port Map on mux device pages"""
        device = self.context["object"]
        # only show for mux devices
        if (
            not hasattr(device, "device_role")
            or device.device_role.slug != MUX_ROLE_SLUG
        ):
            return ""
        # Check if mux has any port mappings first
        if not MuxWavelengthMap.objects.filter(mux=device).exists():
            return ""

        try:
            mux_span = OpticalSpan.objects.get(
                models.Q(mux_a=device) | models.Q(mux_z=device)
            )
        except OpticalSpan.DoesNotExist:
            mux_span = None

        # Get all wavelength mappings for the mux
        mux_port_wavelengths_map = list(
            MuxWavelengthMap.objects.filter(mux=device).select_related(
                "port", "wavelength"
            )
        )

        if mux_span:
            # Get all connections for the span in a single query
            connections_on_span = OpticalConnection.objects.filter(span=mux_span)

            # Create a lookup map from wavelength_id to connection object for fast access
            wavelength_to_connection_map = {
                conn.wavelength_id: conn for conn in connections_on_span
            }

            # Assign connection from the map
            for mapping in mux_port_wavelengths_map:
                mapping.connection = wavelength_to_connection_map.get(
                    mapping.wavelength_id
                )
        else:
            # No span means no connections are possible
            for mapping in mux_port_wavelengths_map:
                mapping.connection = None

        return self.render(
            "netbox_optics/inc/device_mux_port_map.html",
            {"mux_maps": mux_port_wavelengths_map, "device": device, "mux_span": mux_span},
        )


# List of template extensions to register
template_extensions = [DeviceOpticalConnections, InterfaceOpticalConnection, DeviceMuxPortMapTable]

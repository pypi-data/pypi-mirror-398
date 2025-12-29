"""Navigation items in plugins menu for GUI"""

from netbox.plugins import PluginMenuItem, PluginMenuButton
from utilities.choices import ButtonColorChoices

item_grid_types = PluginMenuItem(
    link="plugins:netbox_optics:opticalgridtype_list",
    link_text="Optical Grid Types",
    permissions=["netbox_optics.view_opticalgridtype"],
    buttons=(
        PluginMenuButton(
            link="plugins:netbox_optics:opticalgridtype_add",
            title="Add Optical Grid Type",
            icon_class="mdi mdi-plus-thick",
            color=ButtonColorChoices.GREEN,
            permissions=["netbox_optics.add_opticalgridtype"],
        ),
    ),
)

item_grids = PluginMenuItem(
    link="plugins:netbox_optics:opticalgrid_list",
    link_text="Optical Grids",
    permissions=["netbox_optics.view_opticalgrid"],
    buttons=(
        PluginMenuButton(
            link="plugins:netbox_optics:opticalgrid_add",
            title="Add Optical Grid",
            icon_class="mdi mdi-plus-thick",
            color=ButtonColorChoices.GREEN,
            permissions=["netbox_optics.add_opticalgrid"],
        ),
    ),
)

item_spans = PluginMenuItem(
    link="plugins:netbox_optics:opticalspan_list",
    link_text="Optical Spans",
    permissions=["netbox_optics.view_opticalspan"],
    buttons=(
        PluginMenuButton(
            link="plugins:netbox_optics:opticalspan_add",
            title="Add Optical Span",
            icon_class="mdi mdi-plus-thick",
            color=ButtonColorChoices.GREEN,
            permissions=["netbox_optics.add_opticalspan"],
        ),
    ),
)

item_connections = PluginMenuItem(
    link="plugins:netbox_optics:opticalconnection_list",
    link_text="Optical Connections",
    permissions=["netbox_optics.view_opticalconnection"],
    buttons=(
        PluginMenuButton(
            link="plugins:netbox_optics:opticalconnection_add",
            title="Add Optical Connection",
            icon_class="mdi mdi-plus-thick",
            color=ButtonColorChoices.GREEN,
            permissions=["netbox_optics.add_opticalconnection"],
        ),
    ),
)

item_mux_maps = PluginMenuItem(
    link="plugins:netbox_optics:muxwavelengthmap_list",
    link_text="Mux Wavelength Maps",
    permissions=["netbox_optics.view_muxwavelengthmap"],
    buttons=(
        PluginMenuButton(
            link="plugins:netbox_optics:muxwavelengthmap_add",
            title="Add Mux Wavelength Map",
            icon_class="mdi mdi-plus-thick",
            color=ButtonColorChoices.GREEN,
            permissions=["netbox_optics.add_muxwavelengthmap"],
        ),
    ),
)

menu_items = (item_grid_types, item_grids, item_spans, item_connections, item_mux_maps)

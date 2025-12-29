from netbox.plugins import PluginConfig


class NetBoxOpticsConfig(PluginConfig):
    name = 'netbox_optics'
    verbose_name = 'Optical Connections'
    description = 'Add support for optical connections'
    version = '0.4.4'
    author = 'Konstantin Kudryavtsev'
    author_email = 'kkudryavtsev@dropbox.com'
    base_url = 'optics'
    min_version = '3.7.8'
    max_version = '3.9.99'
    default_settings = {}
    required_settings = []


config = NetBoxOpticsConfig

from dependency.core import Plugin, PluginMeta, module
from example.plugin.hardware.settings import HardwarePluginConfig

@module()
class HardwarePlugin(Plugin):
    meta = PluginMeta(name="HardwarePlugin", version="0.1.0")
    config: HardwarePluginConfig

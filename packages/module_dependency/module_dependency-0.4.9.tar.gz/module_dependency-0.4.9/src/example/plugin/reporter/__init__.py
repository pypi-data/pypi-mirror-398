from dependency.core import Plugin, PluginMeta, module
from example.plugin.reporter.settings import ReporterPluginConfig

@module()
class ReporterPlugin(Plugin):
    meta = PluginMeta(name="ReporterPlugin", version="0.1.0")
    config: ReporterPluginConfig

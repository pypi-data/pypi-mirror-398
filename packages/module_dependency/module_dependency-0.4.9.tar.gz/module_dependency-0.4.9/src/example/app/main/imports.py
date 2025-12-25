from dependency.core import Plugin
from example.plugin.base.imports import BasePlugin
from example.plugin.hardware.imports import HardwarePlugin
from example.plugin.reporter.imports import ReporterPlugin

PLUGINS: list[Plugin] = [
    BasePlugin,
    HardwarePlugin,
    ReporterPlugin
]

from abc import ABC, abstractmethod
from dependency.core import Component, component
from example.plugin.reporter import ReporterPlugin
from example.plugin.reporter.factory.interfaces import Reporter

class ReporterFactory(ABC):
    @abstractmethod
    def createProduct(self, product: str) -> Reporter:
        pass

@component(
    module=ReporterPlugin,
    interface=ReporterFactory,
)
class ReporterFactoryComponent(Component):
    pass

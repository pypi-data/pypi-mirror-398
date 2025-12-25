from abc import ABC, abstractmethod
from dependency.core import Component, component
from example.plugin.reporter import ReporterPlugin

class ReportFacade(ABC):
    @abstractmethod
    def startModule(self) -> None:
        pass

@component(
    module=ReporterPlugin,
    interface=ReportFacade,
)
class ReportFacadeComponent(Component):
    pass

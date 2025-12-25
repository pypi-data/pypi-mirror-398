from dependency_injector.wiring import inject
from dependency.core import instance, providers
from dependency.core.injection import LazyProvide
from example.plugin.reporter import ReporterPlugin
from example.plugin.reporter.facade import ReportFacade, ReportFacadeComponent
from example.plugin.reporter.factory import ReporterFactory, ReporterFactoryComponent
from example.plugin.hardware.bridge import HardwareAbstraction, HardwareAbstractionComponent

@instance(
    component=ReportFacadeComponent,
    imports=[
        ReporterFactoryComponent,
        HardwareAbstractionComponent,
    ],
    provider=providers.Singleton,
    bootstrap=True,
)
class ReporterFacadeA(ReportFacade):
    def __init__(self) -> None:
        self.startModule()
        assert ReporterPlugin.config.config == True
        print("FacadeA initialized")

    @inject
    def startModule(self,
            factory: ReporterFactory = LazyProvide(ReporterFactoryComponent.reference),
            bridge: HardwareAbstraction = LazyProvide(HardwareAbstractionComponent.reference),
        ) -> None:
        reporter = factory.createProduct(product="A")
        bridge.someOperation(product="A")
        bridge.otherOperation(product="B")
        print("reportProducts:", reporter.reportProducts())
        print("reportOperations:", reporter.reportOperations())

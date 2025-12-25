from dependency.core import instance, providers
from example.plugin.reporter.factory import ReporterFactory, ReporterFactoryComponent
from example.plugin.reporter.factory.interfaces import Reporter
from example.plugin.reporter.factory.products.productA import ReporterA

@instance(
    component=ReporterFactoryComponent,
    products=[
        ReporterA,
    ],
    provider=providers.Singleton,
)
class ReporterFactoryCreatorA(ReporterFactory):
    def __init__(self):
        print("FactoryCreatorA initialized")

    def createProduct(self, product: str) -> Reporter:
        instance: Reporter
        match product:
            case "A":
                instance = ReporterA()
                return instance
            case _:
                raise ValueError(f"Unknown product type: {product}")

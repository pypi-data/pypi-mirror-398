from dependency.core import instance, providers
from example.plugin.base.string import StringService, StringServiceComponent

@instance(
    component=StringServiceComponent,
    provider=providers.Singleton,
)
class FakeStringService(StringService):
    def getRandomString(self) -> str:
        return "randomString"

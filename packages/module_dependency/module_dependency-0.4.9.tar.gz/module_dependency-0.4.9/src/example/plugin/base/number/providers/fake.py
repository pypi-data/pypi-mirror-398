from dependency.core import instance, providers
from example.plugin.base.number import NumberService, NumberServiceComponent

@instance(
    component=NumberServiceComponent,
    provider=providers.Singleton
)
class FakeNumberService(NumberService):
    def __init__(self, starting_number: int = 42) -> None:
        self.__number = starting_number

    def getRandomNumber(self) -> int:
        actual_number = self.__number
        self.__number += 1
        return actual_number

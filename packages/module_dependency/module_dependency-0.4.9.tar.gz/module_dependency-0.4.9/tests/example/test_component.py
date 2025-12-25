import pytest
from dependency.core import Container, Entrypoint
from example.plugin.base import BasePlugin
from example.plugin.base.number import NumberService, NumberServiceComponent
from example.plugin.base.number.providers.fake import FakeNumberService

@pytest.fixture
def setup():
    class ExampleApp(Entrypoint):
        def __init__(self) -> None:
            super().__init__(
                container=Container(),
                plugins=[BasePlugin])

    return ExampleApp()

def test_component(setup: object):
    numberService1: NumberService = NumberServiceComponent.provide()
    numberService2: NumberService = NumberServiceComponent.provider()
    assert numberService1 == numberService2
    assert isinstance(numberService1, NumberService)
    assert numberService1.getRandomNumber() == 42
    assert numberService2.getRandomNumber() == 43

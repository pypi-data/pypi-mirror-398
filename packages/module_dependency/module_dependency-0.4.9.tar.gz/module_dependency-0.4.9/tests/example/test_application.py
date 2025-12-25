from dependency.core.resolution import InjectionResolver
from example.app.main import MainApplication

def test_main():
    app = MainApplication()
    loader: InjectionResolver = app.resolver
    assert loader is not None

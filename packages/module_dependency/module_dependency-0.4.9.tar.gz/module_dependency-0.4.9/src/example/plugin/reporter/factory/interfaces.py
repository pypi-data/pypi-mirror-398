from abc import ABC, abstractmethod

class Reporter(ABC):
    @abstractmethod
    def reportProducts(self) -> list[str]:
        pass

    @abstractmethod
    def reportOperations(self) -> list[str]:
        pass

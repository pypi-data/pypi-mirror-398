from abc import ABC, abstractmethod

class Hardware(ABC):
    @abstractmethod
    def doStuff(self, operation: str) -> None:
        pass

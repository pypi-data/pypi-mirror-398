from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

T = TypeVar('T')

class StateMixin(Generic[T]):
    def __init__(self, initial_state: T, **kwargs: Any):
        super().__init__(**kwargs)
        self.__state: T = initial_state

    @property
    def state(self) -> T:
        return self.__state

    @state.setter
    def state(self, state: T) -> None:
        self.__state = state


if __name__ == '__main__':
    class PlayerState(ABC):
        @abstractmethod
        def action(self) -> None:
            pass

    class HasPlayerState(StateMixin[PlayerState]):
        pass

    class PlayerState1(PlayerState):
        def action(self) -> None:
            print("PlayerState1 action")

    class PlayerState2(PlayerState):
        def action(self) -> None:
            print("PlayerState2 action")

    class Player(HasPlayerState):
        def __init__(self) -> None:
            super().__init__(initial_state=PlayerState1())

        def action(self) -> None:
            self.state.action()

    instance = Player()
    instance.action()
    instance.state = PlayerState2()
    instance.action()

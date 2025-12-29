from collections.abc import Iterable
from typing import NewType
from unittest.mock import Mock

from dishka import Provider, Scope, from_context, provide
from dishka.entities.depends_marker import FromDishka

ContextDep = NewType("ContextDep", str)
StepDep = NewType("StepDep", str)

AppDep = NewType("AppDep", str)
APP_DEP_VALUE = AppDep("APP")

RequestDep = NewType("RequestDep", str)
REQUEST_DEP_VALUE = RequestDep("REQUEST")

AppMock = NewType("AppMock", Mock)


class AppProvider(Provider):
    context = from_context(provides=ContextDep, scope=Scope.REQUEST)

    def __init__(self) -> None:
        super().__init__()
        self.app_released = Mock()
        self.request_released = Mock()
        self.mock = Mock()
        self._app_mock = AppMock(Mock())

    @provide(scope=Scope.APP)
    def app(self) -> Iterable[AppDep]:
        yield APP_DEP_VALUE
        self.app_released()

    @provide(scope=Scope.REQUEST)
    def request(self) -> Iterable[RequestDep]:
        yield REQUEST_DEP_VALUE
        self.request_released()

    @provide(scope=Scope.REQUEST)
    def get_mock(self) -> Mock:
        return self.mock

    @provide(scope=Scope.APP)
    def app_mock(self) -> AppMock:
        return self._app_mock

    @provide(scope=Scope.STEP)
    def step(self, request: FromDishka[RequestDep]) -> StepDep:
        return StepDep(f"step for {request}")

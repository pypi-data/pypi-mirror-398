from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any
from unittest.mock import Mock

import pytest
from dishka import make_async_container
from flet import ControlEvent

from dishka_flet import (
    FromDishka,
    inject,
    setup_dishka,
)

from .common import (
    APP_DEP_VALUE,
    REQUEST_DEP_VALUE,
    AppDep,
    AppProvider,
    RequestDep,
)


class MockSession:
    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    def get(self, key: str) -> Any:
        return self._data.get(key)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value


class MockPage:
    def __init__(self) -> None:
        self.session = MockSession()


@dataclass
class MockControlEvent:
    page: MockPage


@asynccontextmanager
async def dishka_page(
    provider: AppProvider,
) -> AsyncIterator[tuple[MockPage, MockControlEvent]]:
    page = MockPage()
    event = MockControlEvent(page)

    container = make_async_container(provider)
    setup_dishka(container, page=page)  # type: ignore[arg-type,unused-ignore]

    yield page, event

    await container.close()


async def handler_with_app(
    event: ControlEvent,  # noqa: ARG001
    a: FromDishka[AppDep],
    mock: FromDishka[Mock],
) -> str:
    mock(a)
    return "passed"


@pytest.mark.asyncio()
async def test_app_dependency(app_provider: AppProvider) -> None:
    async with dishka_page(app_provider) as (_page, event):
        handler = inject(handler_with_app)
        result = await handler(event)  # type: ignore[call-arg]

        assert result == "passed"
        app_provider.mock.assert_called_with(APP_DEP_VALUE)
        app_provider.app_released.assert_not_called()
    app_provider.app_released.assert_called()


async def handler_with_request(
    event: ControlEvent,  # noqa: ARG001
    a: FromDishka[RequestDep],
    mock: FromDishka[Mock],
) -> str:
    mock(a)
    return "passed"


@pytest.mark.asyncio()
async def test_request_dependency(app_provider: AppProvider) -> None:
    async with dishka_page(app_provider) as (_page, event):
        handler = inject(handler_with_request)
        result = await handler(event)  # type: ignore[call-arg]

        assert result == "passed"
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()


async def handler_with_event_as_kwarg(
    event: ControlEvent,  # noqa: ARG001
    a: FromDishka[AppDep],
    mock: FromDishka[Mock],
) -> str:
    mock(a)
    return "passed"


@pytest.mark.asyncio()
async def test_event_as_kwarg(app_provider: AppProvider) -> None:
    async with dishka_page(app_provider) as (_page, event):
        handler = inject(handler_with_event_as_kwarg)
        result = await handler(event=event)  # type: ignore[call-arg]

        assert result == "passed"
        app_provider.mock.assert_called_with(APP_DEP_VALUE)


async def handler_with_event_as_first_arg(
    event: ControlEvent,  # noqa: ARG001
    a: FromDishka[AppDep],
    mock: FromDishka[Mock],
) -> str:
    mock(a)
    return "passed"


@pytest.mark.asyncio()
async def test_event_as_first_arg(app_provider: AppProvider) -> None:
    async with dishka_page(app_provider) as (_page, event):
        handler = inject(handler_with_event_as_first_arg)
        result = await handler(event)  # type: ignore[call-arg]

        assert result == "passed"
        app_provider.mock.assert_called_with(APP_DEP_VALUE)


async def handler_with_event_in_kwargs(
    _some_param: str,
    a: FromDishka[AppDep],
    mock: FromDishka[Mock],
    **kwargs: Any,  # noqa: ARG001
) -> str:
    mock(a)
    return "passed"


@pytest.mark.asyncio()
async def test_event_in_kwargs_values(app_provider: AppProvider) -> None:
    async with dishka_page(app_provider) as (_page, event):
        handler = inject(handler_with_event_in_kwargs)
        result = await handler("test", some_other_param=event)  # type: ignore[call-arg]

        assert result == "passed"
        app_provider.mock.assert_called_with(APP_DEP_VALUE)


@pytest.mark.asyncio()
async def test_missing_event_raises_error(app_provider: AppProvider) -> None:
    async with dishka_page(app_provider) as (_page, _event):
        handler = inject(handler_with_app)

        with pytest.raises(ValueError, match="Cannot find event with page attribute"):
            await handler("not_an_event")  # type: ignore[call-arg]


@pytest.mark.asyncio()
async def test_missing_container_raises_error() -> None:
    page = MockPage()
    event = MockControlEvent(page)

    async def handler_without_setup(
        _event: ControlEvent,
        _a: FromDishka[AppDep],
    ) -> str:
        return "passed"

    handler = inject(handler_without_setup)

    with pytest.raises(ValueError, match="Container not found"):
        await handler(event)  # type: ignore[call-arg]


@pytest.mark.asyncio()
async def test_setup_dishka_stores_container(
    app_provider: AppProvider,
) -> None:
    page = MockPage()
    container = make_async_container(app_provider)

    setup_dishka(container, page=page)  # type: ignore[arg-type,unused-ignore]

    stored_container = page.session.get("dishka_container")
    assert stored_container is container

    await container.close()

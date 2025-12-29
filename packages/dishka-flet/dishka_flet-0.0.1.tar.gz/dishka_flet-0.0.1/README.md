# Flet integration for Dishka

[![Downloads](https://static.pepy.tech/personalized-badge/dishka-flet?period=month&units=international_system&left_color=grey&right_color=green&left_text=downloads/month)](https://www.pepy.tech/projects/dishka-faststream)
[![Package version](https://img.shields.io/pypi/v/dishka-flet?label=PyPI)](https://pypi.org/project/dishka-flet)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/dishka-faststream.svg)](https://pypi.org/project/dishka-flet)

Though it is not required, you can use *dishka-flet* integration. It features:

* *REQUEST* scope management using sessions

You need to specify `@inject` manually.

## Installation

Install using `pip`

```sh
pip install dishka-flet
```

Or with `uv`

```sh
uv add dishka-flet
```

## How to use

1. Import

```python
from dishka_flet import (
    FromDishka,
    inject,
    setup_dishka
)
from dishka import make_async_container, Provider, provide, Scope
```

2. Create provider. You can use `faststream.types.StreamMessage` and `faststream.ContextRepo` as a factory parameter to access on *REQUEST*-scope

```python
class MyProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_greeting_service(self) -> GreetingService:
        return GreetingService(name="Dishka User")

    @provide(scope=Scope.APP)
    def get_counter_service(self) -> CounterService:
        return CounterService()
```

3. Mark those of your handlers parameters which are to be injected with `FromDishka[]`

```python
@inject
async def button_clicked(
        event: ft.ControlEvent,
        greeting: FromDishka[GreetingService],
        counter: FromDishka[CounterService],
) -> None:
    ...
```

4. Setup `dishka` integration.

```python
setup_dishka(container=container, page=page)
```

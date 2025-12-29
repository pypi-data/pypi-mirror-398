import flet as ft
from dishka import Provider, Scope, make_async_container, provide

from dishka_flet import FromDishka, inject, setup_dishka


class GreetingService:
    def __init__(self, name: str = "World") -> None:
        self.name = name

    def greet(self) -> str:
        return f"Hello, {self.name}!"


class CounterService:
    def __init__(self) -> None:
        self.count = 0

    def increment(self) -> int:
        self.count += 1
        return self.count


class MyProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_greeting_service(self) -> GreetingService:
        return GreetingService(name="Dishka User")

    @provide(scope=Scope.APP)
    def get_counter_service(self) -> CounterService:
        return CounterService()


@inject
async def button_clicked(
        event: ft.ControlEvent,
        greeting: FromDishka[GreetingService],
        counter: FromDishka[CounterService],
) -> None:
    count = counter.increment()
    message = greeting.greet()

    text_control = event.page.data["text_control"]
    text_control.value = f"{message} Button clicked {count} time(s)!"
    event.page.update()


async def main(page: ft.Page) -> None:
    page.title = "Dishka + Flet Example"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    provider = MyProvider()
    container = make_async_container(provider)
    setup_dishka(container, page=page)

    text = ft.Text("Click the button!", size=20)

    button = ft.Button(
        "Click me!",
        on_click=button_clicked,
    )

    page.data = {"text_control": text}

    page.add(
        ft.Column(
            [
                text,
                button,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )


if __name__ == "__main__":
    ft.app(main)

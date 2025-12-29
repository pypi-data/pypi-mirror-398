from textual.app import App, ComposeResult
from textual.widgets import ListView, ListItem, Label, Button
from .vault import PasswordEntry
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from .config import Config
from textual.worker import Worker, get_current_worker

c = {
    "index": "#0a5c7a",
    "password": "#f5bc42",
    "name": "#42c5f5",
    "account": "#4275f5"
}


class Confirm(ModalScreen[bool]):
    BINDINGS = [
        ("left", "prev", "Previous"),
        ("right", "next", "Next"),
    ]

    CSS = """
        #dialog {
            padding: 2;
            background: $panel;
            border: thick $error;
            width: 100%;
            align: center middle;
        }

        #message {
            width: 100%;
            text-align: center;
            margin-bottom: 1;
        }

        #buttons {
            width: 100%;
            align: center middle;
        }
        """

    def __init__(self, message: str):
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(self.message, id="message")
            with Horizontal(id="buttons"):
                yield Button("Yes", id="yes", variant="error")
                yield Button("No", id="no")

    def action_next(self) -> None:
        self.focus_next()

    def action_prev(self) -> None:
        self.focus_previous()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "yes")


class ListApp(App):
    CSS = """
    """

    def __init__(self, items: list[PasswordEntry]):
        super().__init__()

        self.items = items

    def compose(self) -> ComposeResult:
        self.list_view = ListView()
        yield self.list_view

    def on_mount(self) -> None:
        self.set_focus(self.query_one(ListView))
        self.refresh_list()

    def refresh_list(self) -> None:
        self.list_view.clear()
        for i, item in enumerate(self.items):
            self.list_view.append(ListItem(Label(f"[{c['index']}]{i}.[/{c['index']}] [{c['name']}]{item.name}[/{c['name']}] | [{c['account']}]{item.account}[/{c['account']}] - [{c['password']}]{item.password}[/{c['password']}]")))


class DeleteApp(ListApp):

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        self.run_worker(self.confirm_delete(event.list_view.index))

    async def confirm_delete(self, index: int):
        confirm = await self.push_screen_wait(Confirm(f"Confirm deletion of \"{self.items[index].name} - {self.items[index].account}\""))
        if confirm:
            del self.items[index]
            self.refresh_list()


class ConfigApp(App):
    CSS = """ """

    def __init__(self):
        super().__init__()
        self.result = None

    def compose(self) -> ComposeResult:
        self.list_view = ListView()
        yield self.list_view

    def on_mount(self) -> None:
        self.set_focus(self.query_one(ListView))
        self.refresh_list()

    def refresh_list(self) -> None:
        self.list_view.clear()
        for item in Config().__dict__().items():
            self.list_view.append(ListItem(Label(
                f"[{c['name']}]{item[0]}[/{c['name']}] = [{c['password']}]{item[1]}[/{c['password']}]"
            )))

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        self.result = list(Config().__dict__().items())[event.list_view.index]
        await self.action_quit()
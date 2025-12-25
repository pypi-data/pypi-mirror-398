from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Button, Label, Markdown
from textual.containers import Grid, Vertical, Center, ScrollableContainer
from textual.screen import Screen
import datetime
import aiohttp
import os

os.makedirs("../../readmes", exist_ok=True)

class DayScreen(Screen):
    """Screen for a day of the advent calendar!"""

    CSS = """
    DayScreen {
        align: center middle;
    }

    #dialog {
        width: 90%;
        height: 90%;
        border: thick $primary;
        background: $surface;
        padding: 2;
        align: center middle;
    }

    #content-container {
        width: 100%;
        height: 1fr;
        margin-bottom: 1;
        border: solid $secondary;
    }
    
    #close {
        width: 20%;
    }
    """

    def __init__(self, day: int) -> None:
        self.day = day
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            with ScrollableContainer(id="content-container"):
                yield Markdown("Loading...", id="markdown")
            with Center():
                yield Button("Close", id="close")

    async def on_mount(self) -> None:
        self.run_worker(self.load_content(), exclusive=True)

    async def load_content(self) -> None:
        cache_path = f"readmes/day_{self.day}.md"
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r") as f:
                    content = f.read()
                self.query_one("#markdown", Markdown).update(content)
                return
            except Exception as e:
                pass

        urls = [
            f"https://raw.githubusercontent.com/hackclub/hackmas-day-{self.day}/main/README.md",
            f"https://raw.githubusercontent.com/hackclub/hackmas-day-{self.day}/master/README.md"
        ]
        
        content = "Not released yet."
        found = False
        
        try:
            async with aiohttp.ClientSession() as session:
                for url in urls:
                    try:
                        async with session.get(url) as response:
                            if response.status == 200:
                                content = await response.text()
                                found = True
                                break
                    except Exception:
                        continue
        except Exception as e:
            content = f"Error connecting to network: {e}"

        if found:
            try:
                with open(cache_path, "w") as f:
                    f.write(content)
            except Exception as e:
                pass

        self.query_one("#markdown", Markdown).update(content)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss()
        event.stop()


class AdventCalendarApp(App):
    """A Textual app for an advent calendar."""

    CSS = """
    Grid {
        grid-size: 4 3;
        grid-gutter: 1 2;
    }

    Grid Button {
        width: 100%;
        height: 100%;
    }

    Grid Button:hover {
        background: $secondary;
    }

    Grid Button.opened {
        background: $success;
    }
    """

    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]
    START_DATE = datetime.date(2025, 12, 13)

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        with Grid():
            for day in range(1, 13):
                yield Button(str(day), id=f"day-{day}")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        button = event.button
        day = str(button.label)
        unlock_day = self.START_DATE + datetime.timedelta(days=int(day) - 1)
        if datetime.date.today() < unlock_day:
            self.notify(f"You will be able to unlock day {day} on {unlock_day}")
            return None
        if not button.has_class("opened"):
            button.add_class("opened")
        self.push_screen(DayScreen(int(day)))

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )


def main():
    app = AdventCalendarApp()
    app.run()


if __name__ == "__main__":
    main()

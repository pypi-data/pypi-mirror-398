import datetime

from textual.app import App, ComposeResult
from textual.containers import Center, Grid, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label


class DayScreen(Screen):
    """Screen for a day of the advent calendar!"""

    CSS = """
        DayScreen {
            align: center middle;
        }

        #dialog {
            width: 50;
            height: auto;
            border: thick $primary;
            background: $surface;
            padding: 2;
            align: center middle;
        }

        #dialog Label {
            width: 100%;
            text-align: center;
            margin-bottom: 1;
        }

        #dialog Button {
            width: auto;
        }
    """

    gifts = {
        1: "A partridge in a pear tree",
        2: "Two turtle doves",
        3: "Three French hens",
        4: "Four calling birds",
        5: "Five golden rings",
        6: "Six geese-a-laying",
        7: "Seven swans a-swimming",
        8: "Eight maids a-milking",
        9: "Nine ladies dancing",
        10: "Ten lords a-leaping",
        11: "Eleven pipers piping",
        12: "Twelve drummers drumming",
        13: "Thirteen GitHub issues",
        14: "Fourteen Python installs",
        15: "Fifteen languages",
        16: "Sixteen hours coding",
        17: "Seventeen days debugging",
        18: "Eighteen merge conflicts",
        19: "Nineteen unmatched brackets",
        20: "Twenty compiler warnings",
        21: "Twenty-one browser windows",
        22: "Twenty-two config files",
        23: "Twenty-three Git commits",
        24: "Twenty-four unit tests",
        25: "Twenty-five segmentation faults (core dumped)",
    }

    def __init__(self, day: int) -> None:
        self.day = day
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(
                f"On day #{str(self.day)} of Hackmas, my true love gave to me:\n{self.gifts.get(self.day)}"
            )
            with Center():
                yield Button("Close", id="close")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss()
        event.stop()


class AdventCalendarApp(App):
    """A Textual app for an advent calendar."""

    CSS = """
    Grid {
        grid-size: 5 5;
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

    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("r", "reset_buttons", "Close all days"),
    ]

    START_DATE = datetime.date(2025, 12, 1)

    def __init__(self) -> None:
        self.days_completed = 0
        super().__init__()

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(show_clock=True)
        with Grid():
            for day in range(1, 26):
                yield Button(str(day), id=f"day-{day}")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "Joshua's Advent Calendar"
        self.sub_title = "0/25 Days Completed"

    def update_status(self) -> None:
        self.sub_title = f"{self.days_completed}/25 Days Completed"

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
            self.days_completed += 1
            self.update_status()
        self.push_screen(DayScreen(int(day)))

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )

    def action_reset_buttons(self) -> None:
        """An action to close all days."""
        all_buttons = self.query("Button")

        for button in all_buttons:
            if button.has_class("opened"):
                button.remove_class("opened")

        self.days_completed = 0
        self.update_status()


def main():
    app = AdventCalendarApp()
    app.run()


if __name__ == "__main__":
    main()

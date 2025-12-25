from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Button, Label, ProgressBar
from textual.containers import Grid, Vertical, Center
from textual.screen import Screen
import datetime
import argparse
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

DEFAULT_GIFTS = {
    "1": "React Workshop!",
    "2": "A Fustering Workshop!",
    "3": "Keyring with Onshape!",
    "4": "Hono Backend!",
    "5": "Full Stack App with Flask!",
    "6": "3D Printable Ruler!",
    "7": "Interactive Christmas Tree!",
    "8": "Automating Cookie Clicker!",
    "9": "TUI in Textual!",
    "10": "No leeks :3",
    "11": "No leeks :p",
    "12": "Still no leeks :3c"
}


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from JSON file."""
    default_config = {
        "start_date": "2025-12-13",
        "theme": "textual-dark",
        "gifts": DEFAULT_GIFTS,
        "grid_size": [4, 3],
        "app_title": "Advent Calendar"
    }

    if config_path is None:
        script_dir = Path(__file__).parent
        config_path = str(script_dir / "config.json")

    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"Loaded config from: {config_path}")

            merged_config = default_config.copy()
            merged_config.update(config)
            return merged_config
        else:
            print(f"Config file not found at {config_path}, using defaults")
            return default_config

    except json.JSONDecodeError as e:
        print(f"Error parsing config file: {e}")
        print("Using default configuration")
        return default_config
    except Exception as e:
        print(f"Error loading config file: {e}")
        print("Using default configuration")
        return default_config


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

    def __init__(self, day: int, gifts: Optional[Dict[str, Any]] = None) -> None:
        self.day = day
        self.gifts = gifts if gifts is not None else DEFAULT_GIFTS
        super().__init__()

    def compose(self) -> ComposeResult:
        day_str = str(self.day)
        gift = self.gifts.get(day_str, f"Gift for day {self.day}")

        with Vertical(id="dialog"):
            yield Label(f"Here's what's in day {day_str}: {gift}")
            with Center():
                yield Button("Close", id="close")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss()
        event.stop()


class AdventCalendarApp(App):
    """A Textual app for an advent calendar."""

    BINDINGS = [("d", "toggle_dark", "Toggle dark mode"),
                ("r", "reset", "Reset all days")]

    CSS = """
    #progress {
        margin: 1;
        height: 1;
        width: 100%;
    }
    
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

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.gifts = self.config.get("gifts", {})

        start_date_str = self.config.get("start_date", "2025-12-13")
        try:
            self.START_DATE = datetime.datetime.strptime(
                start_date_str, "%Y-%m-%d").date()
        except ValueError:
            print(f"Invalid start_date format in config: {start_date_str}")
            self.START_DATE = datetime.date(2025, 12, 13)

        grid_size = self.config.get("grid_size", [4, 3])
        self.grid_cols = grid_size[0]
        self.grid_rows = grid_size[1]
        self.total_days = self.grid_cols * self.grid_rows
        self.CSS = str(self.CSS).replace("grid-size: 4 3;",  # type: ignore
                                         f"grid-size: {self.grid_cols} {self.grid_rows};")

        app_title = self.config.get("app_title", "Advent Calendar")

        super().__init__()
        self.title = app_title

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        with Grid():
            for day in range(1, self.total_days + 1):
                yield Button(str(day), id=f"day-{day}")
        yield ProgressBar(total=self.total_days, show_eta=False, id="progress")
        yield Footer()

    def update_progress(self) -> None:
        """Update the progress bar based on opened days."""
        day_buttons = [btn for btn in self.query(
            "Button") if btn.id is not None and btn.id.startswith("day-")]
        opened_count = len(
            [btn for btn in day_buttons if btn.has_class("opened")])
        progress_bar = self.query_one("#progress", ProgressBar)
        progress_bar.progress = opened_count

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        button = event.button
        day = str(button.label)
        unlock_day = self.START_DATE + datetime.timedelta(days=int(day) - 1)
        if datetime.date.today() < unlock_day:
            self.notify(
                f"You will be able to unlock day {day} on {unlock_day}")
            return None
        if not button.has_class("opened"):
            button.add_class("opened")
            self.update_progress()
        self.push_screen(DayScreen(int(day), self.gifts))

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )

    def action_reset(self) -> None:
        """Reset all days to unopened."""
        for button in self.query(Button):
            if button.id and button.id.startswith("day-"):
                if button.has_class("opened"):
                    button.remove_class("opened")
        progress_bar = self.query_one("#progress", ProgressBar)
        progress_bar.progress = 0
        self.notify("All days have been reset.")


def main():
    parser = argparse.ArgumentParser(description="Advent Calendar TUI")
    parser.add_argument("--config", type=str, help="Path to config file")
    args = parser.parse_args()

    config = load_config(args.config)

    app = AdventCalendarApp(config)

    app.theme = config.get("theme", "textual-dark")

    app.run()


if __name__ == "__main__":
    main()

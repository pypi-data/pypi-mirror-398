#!/usr/bin/env python3
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Header, Footer, TextArea, Label, Input, Button
from textual.binding import Binding
from textual.screen import ModalScreen
import sys
import os

class SaveScreen(ModalScreen):
    """Screen for saving files."""
    CSS = """
    SaveScreen {
        align: center middle;
        background: rgba(0, 10, 30, 0.5);
    }
    #dialog {
        padding: 1;
        width: 60;
        height: auto;
        border: heavy $accent;
        background: $surface;
        border-title-color: $accent;
    }
    Label { margin-bottom: 1; }
    Input { margin-bottom: 1; border: tall $accent; }
    Horizontal { align: center middle; height: auto; }
    """

    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            yield Label("💾 Save File As:")
            yield Input(placeholder="filename.txt", id="filename_input")
            yield Label("Press Enter to Save, Esc to Cancel", classes="help")

    def on_input_submitted(self, message: Input.Submitted) -> None:
        self.dismiss(message.value)

class FernoMac(App):
    """Ferno: The Tahoe Edition."""
    
    CSS = """
    /* macOS Tahoe 'Liquid Glass' Aesthetic */
    $accent: #00f2ff;
    $bg: #0d1b2a;
    $surface: #1b263b;

    Screen {
        background: $bg;
    }

    Header {
        background: $surface;
        color: $accent;
        dock: top;
        height: 3;
        content-align: center middle;
        text-style: bold;
    }

    Footer {
        background: $surface;
        color: white;
        dock: bottom;
    }

    TextArea {
        border: none;
        background: $bg;
        padding: 1;
        color: #e0e1dd;
    }
    
    TextArea:focus {
        border-left: wide $accent;
    }
    """

    TITLE = "Ferno"
    SUB_TITLE = "Text Editor"

    BINDINGS = [
        Binding("ctrl+s", "save", "Save File"),
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+d", "toggle_dark", "Toggle Dark"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield TextArea.code_editor("", language="python", id="editor")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one(TextArea).focus()
        # Check if a file was passed as an argument
        if len(sys.argv) > 1:
            try:
                with open(sys.argv[1], "r") as f:
                    self.query_one(TextArea).load_text(f.read())
                    self.title = f"Ferno - {sys.argv[1]}"
            except FileNotFoundError:
                pass

    def action_save(self) -> None:
        def save_file(filename: str | None) -> None:
            if filename:
                editor = self.query_one(TextArea)
                with open(filename, "w") as f:
                    f.write(editor.text)
                self.notify(f"File saved to {filename}!", title="Success")
                self.title = f"Ferno - {filename}"

        # If we opened a file, save to it. Otherwise ask.
        if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
            save_file(sys.argv[1])
        else:
            self.push_screen(SaveScreen(), save_file)

def main():
    app = FernoMac()
    app.run()

if __name__ == "__main__":
    main()

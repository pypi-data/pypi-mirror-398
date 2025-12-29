from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Input, Button, Static, Label, ListView, ListItem, TabbedContent, TabPane
from textual.screen import ModalScreen
from textual import on
from rich.text import Text
import json
import os

# Define file path relative to this script
DATA_FILE = os.path.join(os.path.dirname(__file__), "dictionary_data.json")

def load_dictionary():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_dictionary(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        return True
    except Exception:
        return False

class AddWordModal(ModalScreen):
    """Modal to add a new word."""
    CSS = """
    AddWordModal {
        align: center middle;
    }
    #dialog {
        grid-size: 2;
        grid-gutter: 1 2;
        grid-rows: 1fr 3;
        padding: 0 1;
        width: 60;
        height: 11;
        border: thick $background 80%;
        background: $surface;
    }
    #question {
        column-span: 2;
        height: 1fr;
        width: 1fr;
        content-align: center middle;
    }
    #new_translation {
        column-span: 2;
        width: 1fr;
    }
    """

    def __init__(self, word: str):
        super().__init__()
        self.word = word

    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            yield Label(f"Word '{self.word}' not found.\nEnter translation to add it:", id="question")
            yield Input(placeholder="Translation", id="new_translation")
            yield Button("Add", variant="primary", id="add_btn")
            yield Button("Cancel", variant="error", id="cancel_btn")

    @on(Button.Pressed, "#add_btn")
    def add_word(self):
        translation = self.query_one("#new_translation").value.strip()
        if translation:
            self.dismiss((self.word, translation))
        else:
            self.dismiss(None)

    @on(Button.Pressed, "#cancel_btn")
    def cancel(self):
        self.dismiss(None)

class Banglish(App):
    """A Textual app for the Banglish Dictionary."""
    CSS = """
    Screen {
        layout: vertical;
    }
    .box {
        height: 100%;
        border: solid green;
    }
    #search_input {
        dock: top;
        margin: 1;
    }
    #result_panel {
        height: 1fr;
        border: heavy $accent;
        padding: 1 2;
        text-align: center;
        content-align: center middle;
        text-style: bold;
    }
    """
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("b", "browse", "Browse All"),
        ("s", "search", "Search"),
        ("enter", "submit", "Add/Search"),
    ]

    def __init__(self):
        super().__init__()
        self.translations = load_dictionary()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()
        
        with TabbedContent(id="tabs", initial="search_tab"):
            with TabPane("Search", id="search_tab"):
                yield Input(placeholder="Type a Banglish word...", id="search_input")
                yield Static("Welcome! Type a word above.", id="result_panel")
            
            with TabPane("Browse All", id="browse_tab"):
                yield ListView(id="word_list")

    def action_browse(self):
        self.query_one("#tabs").active = "browse_tab"
        self.query_one("#word_list").focus()

    def action_search(self):
        self.query_one("#tabs").active = "search_tab"
        self.query_one("#search_input").focus()
    
    def on_mount(self):
        self.refresh_list()

    def refresh_list(self):
        """Populates the list view with themed words."""
        list_view = self.query_one("#word_list")
        list_view.clear()
        
        sorted_words = sorted(self.translations.items())
        
        for word, meaning in sorted_words:
            # Heuristic coloring
            color = "white"
            m_lower = meaning.lower()
            if "sister" in m_lower or "brother" in m_lower or "mother" in m_lower or "father" in m_lower:
                color = "magenta"
            elif "love" in m_lower or "heart" in m_lower:
                color = "red"
            elif "tree" in m_lower or "flower" in m_lower or "nature" in m_lower or "green" in m_lower:
                color = "green"
            elif "water" in m_lower or "river" in m_lower or "sea" in m_lower or "blue" in m_lower:
                color = "cyan"
            elif "food" in m_lower or "eat" in m_lower or "cook" in m_lower:
                color = "yellow"
            
            styled_text = Text(f"{word.capitalize()} = {meaning}", style=color)
            list_view.append(ListItem(Label(styled_text)))

    @on(Input.Submitted, "#search_input")
    def search_word(self, event: Input.Submitted):
        word = event.value.strip().lower()
        if not word:
            return

        result_panel = self.query_one("#result_panel")
        
        if word in self.translations:
            meaning = self.translations[word]
            result_panel.update(Text(f"\nWord: {word.capitalize()}\n\nMeaning: {meaning}", justify="center", style="bold green white_on_black"))
        else:
            result_panel.update(Text(f"Word '{word}' not found.", style="bold red"))
            self.push_screen(AddWordModal(word), self.on_add_word_result)
        
        event.input.value = ""

    def on_add_word_result(self, result):
        """Callback when Add Word modal closes."""
        if result:
            word, translation = result
            self.translations[word] = translation
            if save_dictionary(self.translations):
                self.query_one("#result_panel").update(Text(f"Added: {word} -> {translation}", style="bold green"))
                self.refresh_list() # Update list
                self.notify(f"Added '{word}' to dictionary!")
            else:
                self.query_one("#result_panel").update(Text("Error saving dictionary!", style="bold red"))

if __name__ == "__main__":
    app = BanglishStart()
    app.run()

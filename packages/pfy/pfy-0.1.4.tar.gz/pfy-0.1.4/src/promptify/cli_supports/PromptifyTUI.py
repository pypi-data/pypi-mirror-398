"""
Promptify CLI v1.0 with Interactive TUI and Inline Editing
"""
import pyperclip

from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Header, Footer, Button, Static, TextArea
from textual.binding import Binding


class PromptifyTUI(App):
    """Interactive Promptify TUI with editing and copy functionality"""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #result-container {
        height: 100%;
        border: solid $primary;
        margin: 1;
    }
    
    #title {
        background: $primary;
        color: $text;
        padding: 0 1;
        text-style: bold;
    }
    
    #result-text {
        height: 1fr;
        background: $surface-darken-1;
        padding: 1;
        border: solid $accent;
    }
    
    #button-bar {
        height: auto;
        dock: bottom;
        background: $panel;
        padding: 1;
    }
    
    Button {
        margin: 0 1;
    }
    
    .modified {
        background: $warning;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("c", "copy", "Copy"),
        Binding("e", "toggle_edit", "Edit Mode"),
        Binding("ctrl+s", "save", "Save", show=False),
    ]
    
    def __init__(self, result_text: str):
        super().__init__()
        self.original_text = result_text
        self.result_text = result_text
        self.is_editing = False
        self.is_modified = False
    
    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="result-container"):
            yield Static(" PROMPTIFIED [Read-Only]", id="title")
            yield TextArea(
                self.result_text,
                id="result-text",
                read_only=True,  # Start in read-only mode
                show_line_numbers=True,
                theme="monokai",  # Optional: syntax highlighting
            )
            with Horizontal(id="button-bar"):
                yield Button(" Edit", variant="primary", id="edit-btn")
                yield Button(" Copy", variant="success", id="copy-btn")
                yield Button(" Save", variant="warning", id="save-btn", disabled=True)
                yield Button("↺ Reset", variant="default", id="reset-btn", disabled=True)
                yield Button("✖ Close", variant="error", id="close-btn")
        yield Footer()
    
    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        """Track if content has been modified"""
        if self.is_editing:
            self.is_modified = (event.text_area.text != self.original_text)
            self._update_ui_state()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks"""
        button_actions = {
            "edit-btn": self.action_toggle_edit,
            "copy-btn": self.action_copy,
            "save-btn": self.action_save,
            "reset-btn": self.action_reset,
            "close-btn": self.exit,
        }
        
        action = button_actions.get(event.button.id)
        if action:
            action()
    
    def action_toggle_edit(self) -> None:
        """Toggle between read-only and edit mode"""
        text_area = self.query_one("#result-text", TextArea)
        title = self.query_one("#title", Static)
        edit_btn = self.query_one("#edit-btn", Button)
        
        self.is_editing = not self.is_editing
        text_area.read_only = not self.is_editing
        
        if self.is_editing:
            title.update("EDITING MODE - Make your changes")
            edit_btn.label = "View"
            text_area.focus()
            self.notify("Edit mode enabled. Press Ctrl+S to save.", severity="information")
        else:
            title.update("PROMPTIFIED [Read-Only]")
            edit_btn.label = "Edit"
            self.notify("Switched to read-only mode.", severity="information")
        
        self._update_ui_state()
    
    def action_copy(self) -> None:
        """Copy current text to clipboard"""
        try:
            text_area = self.query_one("#result-text", TextArea)
            current_text = text_area.text
            pyperclip.copy(current_text)
            self.notify("✔ Copied to clipboard!", severity="information")
        except Exception as e:
            self.notify(f"✖ Copy failed: {e}", severity="error")
    
    def action_save(self) -> None:
        """Save edited text as new result"""
        if not self.is_modified:
            self.notify("No changes to save.", severity="warning")
            return
        
        text_area = self.query_one("#result-text", TextArea)
        self.result_text = text_area.text
        self.original_text = self.result_text
        self.is_modified = False
        
        self._update_ui_state()
        self.notify("✔ Changes saved!", severity="success")
    
    def action_reset(self) -> None:
        """Discard changes and restore original text"""
        text_area = self.query_one("#result-text", TextArea)
        text_area.text = self.original_text
        self.is_modified = False
        
        self._update_ui_state()
        self.notify("↺ Reset to original text.", severity="information")
    
    def _update_ui_state(self) -> None:
        """Update button states based on editing mode and modifications"""
        save_btn = self.query_one("#save-btn", Button)
        reset_btn = self.query_one("#reset-btn", Button)
        title = self.query_one("#title", Static)
        
        # Enable save/reset only when editing and modified
        save_btn.disabled = not (self.is_editing and self.is_modified)
        reset_btn.disabled = not (self.is_editing and self.is_modified)
        
        # Visual indicator for unsaved changes
        if self.is_modified:
            title.add_class("modified")
            title.update("EDITING MODE - Unsaved Changes")
        else:
            title.remove_class("modified")
            if self.is_editing:
                title.update("EDITING MODE - Make your changes")

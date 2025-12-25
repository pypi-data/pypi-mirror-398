# todo: write documentation

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Button, Input
from textual.containers import Horizontal, Vertical
from textual.binding import Binding
# from textual.reactive import reactive - for clock widget
from tkinter import filedialog
import importlib.resources as pkg_resources
import todolist_angrypig555
# import datetime
import re

todo_list = []

def clean_text(text: str) -> str:
    """Remove any markup tags from the text."""
    text = re.sub(r"\[.*?\]", "", text)
    text = text.replace("✅", "")
    return text.strip()



# class Clock(Static):
#    time: reactive[str] = reactive("")
#    def on_mount(self):
#        self.set_interval(1, self.update_time)
#        self.styles.dock = "bottom"
#        self.styles.align = ("right", "bottom")
#        self.styles.padding = (0, 2)
#    def update_time(self):
#        self.time = datetime.datetime.now().strftime("%H:%M:%S")
#        self.update(self.time)
# todo: create a clock widget that doesnt make the whole app mushed

class application(App):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Load TCSS content from package resource
        with pkg_resources.open_text(todolist_angrypig555, "main.tcss") as f:
            css_content = f.read()
        self.stylesheet.add_source(css_content)  # load CSS directly from str
        self.buttons_hidden = False

    BINDINGS = [
        Binding("q", "quit", "Quit the app"),
        Binding("h", "toggle_buttons()", "Hide/Show buttons")]
    
    TITLE = "To-Do List"


    # defines the widgets
    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Enter a new to-do item:", id="label")
        yield Input(placeholder="New to-do item...", id="todo_input")
        yield Horizontal(
            Button("Add Item", id="add_button"),
            Button("Check off item", id="check_button"),
            Button("Export", id="export_button"),
            Button("Import", id="import_button"),
            Button("Remove Item", id="remove_button"),
            id="button_row"
        )
        yield Static("Your To-Do List:", id="list_label")
        yield Static("", id="progress")
        yield Static("No items in the to-do list.", id="todo_list")
        yield Static("To-Do List v1.1. Merry christmas! 🎄", id="custom_footer")
        yield Footer()


    # this updates the progress bar
    def update_progress(self) -> None:
        progress_widget = self.query_one("#progress", Static)

        total = len(todo_list)
        completed = sum("✅" in item for item in todo_list)

        if total == 0:
            progress_widget.update("")
            return

        percent = int((completed / total) * 100)
        filled = int((completed / total) * 20)
        bar = "█" * filled + "░" * (20 - filled)

        progress_widget.update(
            f"[{bar}] {completed}/{total} ({percent}%)"
        )
    # this updates the todo list
    def update_todo_list(self) -> None:
        todo_list_widget = self.query_one("#todo_list", Static)
        if todo_list:
            todo_list_widget.update("\n".join(f"- {item}" for item in todo_list))
        else:
            todo_list_widget.update("Yay, no items in the to-do list!")
        self.update_progress()

    #this exports the todo list into a txt file
    def export_todo_list(self) -> None:
        file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                                 filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if file_path:
            with open(file_path, "w", encoding="utf-8") as file:
                for item in todo_list:
                    file.write(f"{item}\n")
    # this imports the todo list from a txt file
    def import_todo_list(self) -> None:
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if file_path:
            with open(file_path, "r", encoding="utf-8") as file:
                for line in file:
                    item = line.strip()
                    if item and item not in todo_list:
                        todo_list.append(item)
            self.update_todo_list()
    # this handles all of the buttons in the code
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add_button":
            input_widget = self.query_one("#todo_input", Input)
            new_item = input_widget.value.strip()
            if new_item:
                todo_list.append(new_item)
                input_widget.value = ""
                self.update_todo_list()
        elif event.button.id == "remove_button":
            input_widget = self.query_one("#todo_input", Input)
            item_to_remove = input_widget.value.strip()
            for item in todo_list:
                if clean_text(item) == item_to_remove:
                    item_to_remove = item
                    break
            if item_to_remove in todo_list:
                todo_list.remove(item_to_remove)
                input_widget.value = ""
                self.update_todo_list()
        elif event.button.id == "export_button":
            self.export_todo_list()
        elif event.button.id == "import_button":
            self.import_todo_list()
        elif event.button.id == "check_button":
            input_widget = self.query_one("#todo_input", Input)
            item_to_check = input_widget.value.strip()
            if item_to_check in todo_list:
                index = todo_list.index(item_to_check)
                todo_list[index] = f"[strike]{item_to_check}[/strike]✅"
                input_widget.value = ""
                self.update_todo_list()
        


    # this handles the visibility of the buttons and input fields
    def action_toggle_buttons(self) -> None:
        print("Toggling button visibility")
        button_row =self.query_one("#button_row", Horizontal)
        self.buttons_hidden = not self.buttons_hidden
        button_row.visible = not self.buttons_hidden
        todo_input = self.query_one("#todo_input", Input)
        label = self.query_one("#label", Static)
        if self.buttons_hidden:
            label.display = False
            todo_input.display = False
            button_row.display = False  # Hides and removes from layout
            self.notify("Buttons hidden", severity="warning")
        else:
            label.display = True
            todo_input.display = True
            button_row.display = True   # Shows again
            self.notify("Buttons shown", severity="information")

        self.refresh()
            
if __name__ == "__main__":
    app = application()
    app.run()

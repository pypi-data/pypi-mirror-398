from .Calculator import calc
from textual.app import App, ComposeResult
from textual.widgets import Button, Input, Static, Header, Footer
from textual.containers import Grid, Vertical, Container
from textual.binding import Binding

class ScienceCalc(App):
    """A fully responsive, screen-filling Scientific Calculator."""
    
    CSS = """
    Screen {
        align: center middle;
        background: #0f172a;
        padding: 0;
        margin: 0;
    }

    #calculator {
        width: 100%;
        height: 100%;
        border: thick #38bdf8;
        background: #1e293b;
        color: white;
        padding: 1;
        layout: vertical;
    }

    #display-area {
        height: 20%;
        min-height: 5;
        background: #020617;
        border: tall #38bdf8;
        margin-bottom: 1;
        padding: 0 1;
        layout: vertical;
    }

    #input {
        background: transparent;
        border: none;
        color: #94a3b8;
        height: 1;
        width: 100%;
        padding: 0;
        content-align: right middle;
    }

    #input:focus {
        border: none;
    }

    #result {
        color: #38bdf8;
        content-align: right middle;
        text-style: bold;
        height: 1fr;
        padding-right: 1;
    }

    Grid {
        grid-size: 5;
        grid-gutter: 1;
        height: 75%;
    }

    Button {
        width: 100%;
        height: 1fr;
        border: none;
        text-style: bold;
    }

    .number {
        background: #334155;
    }

    .number:hover {
        background: #475569;
    }

    .operator {
        background: #0ea5e9;
        color: white;
    }

    .operator:hover {
        background: #38bdf8;
    }

    .func {
        background: #6366f1;
        color: white;
    }

    .func:hover {
        background: #818cf8;
    }

    #btn-calculate {
        background: #10b981;
        column-span: 2;
    }

    #btn-calculate:hover {
        background: #34d399;
    }

    #btn-clear {
        background: #ef4444;
        column-span: 2;
    }

    #btn-clear:hover {
        background: #f87171;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("^d", "clear", "Clear"),
        
        Binding("enter", "calculate", "Calculate"),
        
        

    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="calculator"):
            with Vertical(id="display-area"):
                yield Input(placeholder="Type here...", id="input")
                yield Static("0", id="result")
            
            with Grid():
                # Scientific Row
                yield Button("sin", classes="func")
                yield Button("cos", classes="func")
                yield Button("tan", classes="func")
                yield Button("ln", classes="func")
                yield Button("log", classes="func")

                # Constants & Power
                yield Button("pi", classes="func")
                yield Button("e", classes="func")
                yield Button("√", classes="operator")
                yield Button("^", classes="operator")
                yield Button("/", classes="operator")

                # Pad 1
                yield Button("7", classes="number")
                yield Button("8", classes="number")
                yield Button("9", classes="number")
                yield Button("X", classes="operator")
                yield Button("(", classes="operator")

                # Pad 2
                yield Button("4", classes="number")
                yield Button("5", classes="number")
                yield Button("6", classes="number")
                yield Button("-", classes="operator")
                yield Button(")", classes="operator")

                # Pad 3
                yield Button("1", classes="number")
                yield Button("2", classes="number")
                yield Button("3", classes="number")
                yield Button("+", classes="operator")
                yield Button("%", classes="operator")

                # Bottom Row
                yield Button("0", classes="number")
                yield Button(".", classes="number")
                yield Button("CLR", id="btn-clear")
                yield Button("ENTER", id="btn-calculate")

    def on_mount(self) -> None:
        self.query_one("#input").focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        input_widget = self.query_one("#input", Input)
        btn = event.button
        label = str(btn.label)

        if btn.id == "btn-calculate":
            self.action_calculate()
        elif btn.id == "btn-clear":
            self.action_clear()
        else:
            if btn.has_class("func") and label not in ["pi", "e"]:
                input_widget.value += f"{label}("
            else:
                char_map = {"X": "*", "√": "√", "ENTER": ""}
                char = char_map.get(label, label)
                input_widget.value += char
        
        input_widget.focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.action_calculate()

    def action_calculate(self) -> None:
        input_val = self.query_one("#input", Input).value
        if input_val:
            res_val = calc(input_val)
            self.query_one("#result", Static).update(res_val)

    def action_clear(self) -> None:
        self.query_one("#input", Input).value = ""
        self.query_one("#result", Static).update("0")

if __name__ == "__main__":
    app = ScienceCalc()
    app.run()
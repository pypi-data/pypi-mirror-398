import os
from textual.app import App
from textual.containers import Container
from textual.reactive import reactive

from .sections import battery, cpu, memory, network, processes, storage

os.environ["COLORTERM"] = "truecolor"

class Pulse(App):
    CSS = """
    Screen {
        background: rgb(25, 25, 25);
        padding: 1 2;
    }

    .cards {
        layout: grid;
        grid-size: 2;
        grid-gutter: 1 4;
        height: auto;
    }

    .card {
        border: round rgb(255, 255, 255);
        height: auto;
        padding: 1 4;
        border-title-align: center;
        align: center middle;
    }

    #cpu, #processes {
        column-span: 2;
    }

    #memory {
        row-span: 3;
    }

    .cards.stacked {
        grid-size: 1; 
    }

    .cards.stacked #cpu, 
    .cards.stacked #processes {
        column-span: 1;
    }

    .cards.stacked #memory {
        row-span: 1;
    }
    """

    narrow = reactive(False)

    def compose(self):
        with Container(classes = "cards"):
            yield cpu.CPU(classes = "card", id = "cpu", title = "CPU")
            yield memory.Memory(classes = "card", id = "memory", title = "Memory")
            yield network.Network(classes = "card", id = "network", title = "Network")
            yield battery.Battery(classes = "card", id = "battery", title = "Battery")
            yield storage.Storage(classes = "card", id = "storage", title = "Storage")
            yield processes.Processes(classes = "card", id = "processes", title = "Processes")

    def on_mount(self):
        self.call_after_refresh(self.screen.scroll_home, animate = False)

    def on_resize(self, event):
        self.narrow = event.size.width < 110

    def watch_narrow(self, narrow):
        self.query_one(".cards").set_class(narrow, "stacked")

def run():
    app = Pulse()
    app.run()

if __name__ == "__main__":
    run()
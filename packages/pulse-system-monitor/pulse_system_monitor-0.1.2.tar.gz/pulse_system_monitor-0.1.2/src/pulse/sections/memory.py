from psutil import virtual_memory, swap_memory
from textual.containers import Container
from textual.widgets import Label
from textual.reactive import reactive

from ..plot import Plot

class Memory(Container):
    DEFAULT_CSS = """
    Memory {
        height: auto;
    }

    .info {
        layout: grid;
        grid-size: 2;
        grid-gutter: 1 0;
        height: auto;
    }

    #virtual-memory-plot {
        height: 13;
        column-span: 2;
        margin-bottom: 1;
    }

    #used-memory, #total-memory {
        width: 1fr;
        content-align: left middle;
    }

    #used-swap, #total-swap {
        width: 1fr;
        content-align: right middle;
    }

    .info.stacked {
        grid-size: 1; 
    }

    .info.stacked #used-memory,
    .info.stacked #used-swap,
    .info.stacked #total-memory,
    .info.stacked #total-swap {
        content-align: left middle;
    }
    """

    narrow = reactive(False)

    def __init__(self, classes, id, title):
        super().__init__(classes = classes, id = id)
        self.border_title = title
        self.history = [0.0] * 60

    def compose(self):
        yield Plot(id = "virtual-memory-plot")

        with Container(classes = "info"):
            yield Label(id = "used-memory")
            yield Label(id = "used-swap")
            yield Label(id = "total-memory")
            yield Label(id = "total-swap")
    
    def on_mount(self):
        self.update_data()
        self.set_interval(1.0, self.update_data)

    def update_data(self):
        virtual_memory_info = virtual_memory()
        swap_memory_info = swap_memory()

        used_virtual_memory = round(virtual_memory_info.used / (1024 ** 3), 2)
        total_virtual_memory = round(virtual_memory_info.total / (1024 ** 3), 2)

        self.history.append(used_virtual_memory)
        self.history.pop(0)

        graph = self.query_one("#virtual-memory-plot", Plot).create()

        graph.clear_figure()
        
        graph.plot(self.history, marker = "braille", fillx = True, color = (220, 60, 100))
        graph.title("Memory Usage (GB)")
        graph.ylim(0, total_virtual_memory)
        graph.yticks([0, round(total_virtual_memory / 2, 2), total_virtual_memory])
        graph.xticks([0, 30, 60])
        graph.canvas_color((25, 25, 25))
        graph.ticks_color((255, 255, 255))
        graph.axes_color((25, 25, 25))

        self.query_one("#virtual-memory-plot", Plot).refresh()

        self.query_one("#used-memory", Label).update(f"Used memory: {used_virtual_memory} GB")
        self.query_one("#total-memory", Label).update(f"Total memory: {total_virtual_memory} GB")

        used_swap_memory = round(swap_memory_info.used / (1024 ** 3), 2)
        total_swap_memory = round(swap_memory_info.total / (1024 ** 3), 2)

        self.query_one("#used-swap", Label).update(f"Used swap: {used_swap_memory} GB")
        self.query_one("#total-swap", Label).update(f"Total swap: {total_swap_memory} GB")

    def on_resize(self):
        self.narrow = self.app.size.width < 60

    def watch_narrow(self, narrow):
        self.query_one(".info").set_class(narrow, "stacked")
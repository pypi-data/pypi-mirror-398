from textual.containers import Container
from textual.widgets import Label, ProgressBar
from textual.reactive import reactive
from psutil import cpu_count, cpu_freq, cpu_percent

class CPU(Container):
    DEFAULT_CSS = """
    CPU {
        layout: grid;
        grid-size: 4;
        grid-gutter: 1 4;
        height: auto;
    }
    
    .core-info {
        layout: horizontal;
        height: auto;
    }

    .core-bar Bar > .bar--bar, .core-bar Bar > .bar--complete {
        color: rgb(220, 140, 220);
        background: rgb(80, 30, 80);
    }

    #cpu-usage {
        width: 1fr;
        content-align: left middle;
        column-span: 2;
    }

    #frequency {
        width: 1fr;
        content-align: right middle;
        column-span: 2;
    }

    CPU.two-columns {
        grid-size: 2; 
    }

    CPU.two-columns #cpu-usage,
    CPU.two-columns #frequency {
        column-span: 1;
    }

    CPU.stacked {
        grid-size: 1; 
    }

    CPU.stacked #cpu-usage,
    CPU.stacked #frequency {
        content-align: left middle;
    }
    """

    narrow = reactive(False)
    very_narrow = reactive(False)

    def __init__(self, classes, id, title):
        super().__init__(classes = classes, id = id)
        self.border_title = title

    def compose(self):
        for i in range(cpu_count()):
            with Container(classes = "core-info"):
                yield Label(f"Core {i + 1}  ", classes = "core-label")
                yield ProgressBar(total = 100, show_eta = False, show_percentage = False, id = f"core-bar-{i + 1}", classes = "core-bar")

        yield Label(id = "cpu-usage")
        yield Label(id = "frequency")

    def on_mount(self):
        self.update_data()
        self.set_interval(1.0, self.update_data)

    def update_data(self):
        per_core_usage = cpu_percent(percpu = True)
        average_usage = sum(per_core_usage) / len(per_core_usage)
        
        for i, usage in enumerate(per_core_usage):
            self.query_one(f"#core-bar-{i + 1}", ProgressBar).update(progress = usage)
        
        self.query_one("#cpu-usage", Label).update(f"Usage: {average_usage:.2f}%")
        self.query_one("#frequency", Label).update(f"Frequency: {cpu_freq().current:.2f} MHz")

    def on_resize(self):
        self.narrow = self.app.size.width < 80
        self.very_narrow = self.app.size.width < 60

    def watch_narrow(self, narrow):
        self.set_class(narrow, "two-columns")

    def watch_very_narrow(self, very_narrow):
        self.set_class(very_narrow, "stacked")
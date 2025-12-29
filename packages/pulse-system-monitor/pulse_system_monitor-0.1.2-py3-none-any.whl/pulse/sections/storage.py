from textual.containers import Container
from textual.widgets import Label, ProgressBar
from textual.reactive import reactive
from psutil import disk_partitions, disk_usage

class Storage(Container):
    DEFAULT_CSS = """
    Storage {
        layout: grid;
        grid-size: 2;
        grid-gutter: 1 0;
        height: auto;
    }

    #storage-bar {
        column-span: 2;
    }

    #storage-bar Bar {
        width: 1fr;
    }

    #storage-bar Bar > .bar--bar, #storage-bar Bar > .bar--complete {
        color: rgb(50, 140, 220);
        background: rgb(20, 50, 100);
    }

    #used {
        width: 1fr;
        content-align: left middle;
    }

    #total {
        width: 1fr;
        content-align: right middle;
    }

    Storage.stacked {
        grid-size: 1; 
    }

    Storage.stacked #storage-bar {
        column-span: 1;
    }

    Storage.stacked #used,
    Storage.stacked #total {
        content-align: left middle;
    }
    """

    narrow = reactive(False)

    def __init__(self, classes, id, title):
        super().__init__(classes = classes, id = id)
        self.border_title = title

    def compose(self):
        yield ProgressBar(
            total = 100,
            show_percentage = True,
            show_eta = False,
            id = "storage-bar"
        )

        yield Label(id = "used")
        yield Label(id = "total")

    def on_mount(self):
        partitions = disk_partitions(all = False)
    
        total = 0
        used = 0

        for partition in partitions:
            usage = disk_usage(partition.mountpoint)
            total += usage.total
            used += usage.used

        bar = self.query_one("#storage-bar", ProgressBar)
        bar.update(progress = (used / total) * 100)

        self.query_one("#used", Label).update(f"Used: {(used / 1024 ** 3):.2f} GB")
        self.query_one("#total", Label).update(f"Total: {(total / 1024 ** 3):.2f} GB")

    def on_resize(self):
        self.narrow = self.app.size.width < 50

    def watch_narrow(self, narrow):
        self.set_class(narrow, "stacked")
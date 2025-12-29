from textual.widgets import DataTable
from textual.containers import Container
from psutil import process_iter
from datetime import datetime

class Processes(Container):
    DEFAULT_CSS = """
    #process-table {
        width: auto;
        max-width: 100%;
        background: rgb(25, 25, 25);
        border: round rgb(220, 150, 80);
        padding-left: 1;
        padding-right: 1;
        background-tint: transparent 0%;
        scrollbar-size-horizontal: 0;
        scrollbar-size-vertical: 0;
    }

    #process-table > .datatable--header {
        background: rgb(25, 25, 25);
        background-tint: transparent 0%;
        text-style: none;
        color: rgb(220, 150, 80);
    }

    #process-table > .datatable--cursor {
        color: rgb(25, 25, 25);
        text-style: bold;
        background: rgb(220, 150, 80);
        background-tint: transparent 0%;
    }
    """

    def __init__(self, classes, id, title):
        super().__init__(classes = classes, id = id)
        self.border_title = title

    def compose(self):
        yield DataTable(cursor_type = "cell", id = "process-table")

    def on_mount(self):
        table = self.query_one("#process-table")

        table.add_columns(
            "Process ID",
            "Process name",
            "Owner",
            "Status",
            "CPU utilization",
            "Memory (MB)",
            "Threads",
            "Creation time",
        )

        self.update_data()
        self.set_interval(5.0, self.update_data)

    def update_data(self):
        table = self.query_one("#process-table")

        scroll_x = table.scroll_x
        scroll_y = table.scroll_y
        cursor_coordinate = table.cursor_coordinate

        table.clear()
        
        for process in process_iter(["pid", "name", "username", "status", "cpu_percent", "memory_info", "num_threads", "create_time"]):
            table.add_row(
                process.info["pid"],
                process.info["name"],
                process.info["username"],
                process.info["status"],
                process.info["cpu_percent"],
                round(process.info["memory_info"].rss / (1024 * 1024), 2),
                process.info["num_threads"],
                datetime.fromtimestamp(process.info["create_time"]).strftime("%Y-%m-%d %H:%M:%S"),
            )

        table.scroll_x = scroll_x
        table.scroll_y = scroll_y

        table.move_cursor(
            row = cursor_coordinate.row, 
            column = cursor_coordinate.column, 
            animate = False
        )
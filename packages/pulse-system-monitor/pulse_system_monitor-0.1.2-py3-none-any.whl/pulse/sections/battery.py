from textual.containers import Container
from textual.widgets import Label, ProgressBar
from textual.reactive import reactive
from psutil import sensors_battery

class Battery(Container):
    DEFAULT_CSS = """
    Battery {
        layout: grid;
        grid-size: 2;
        grid-gutter: 1 0;
        height: auto;
    }

    #battery-percentage {
        column-span: 2;
    }

    #battery-percentage Bar {
        width: 1fr;
    }

    #battery-percentage Bar > .bar--bar, #battery-bar Bar > .bar--complete {
        color: rgb(100, 220, 100);
        background: rgb(220, 100, 100);
    }

    #charging-status {
        width: 1fr;
        content-align: left middle;
    }

    #time-remaining {
        width: 1fr;
        content-align: right middle;
    }

    Battery.stacked {
        grid-size: 1; 
    }

    Battery.stacked #battery-percentage {
        column-span: 1;
    }

    Battery.stacked #charging-status,
    Battery.stacked #time-remaining {
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
            id = "battery-percentage"
        )

        yield Label(id = "charging-status")
        yield Label(id = "time-remaining")

    def on_mount(self):
        self.update_data()
        self.set_interval(10.0, self.update_data)

    def update_data(self):
        battery = sensors_battery()

        bar = self.query_one("#battery-percentage", ProgressBar)
        bar.update(progress = battery.percent)

        self.query_one("#charging-status", Label).update(f"Charging: {battery.power_plugged}")

        hours_remaining = battery.secsleft // 3600
        minutes_remaining = (battery.secsleft // 60) - (hours_remaining * 60)

        if hours_remaining != 0:
            self.query_one("#time-remaining", Label).update(f"Time remaining: {hours_remaining} hr {minutes_remaining} min")
        else:
            self.query_one("#time-remaining", Label).update(f"Time remaining: {minutes_remaining} min")

    def on_resize(self):
        self.narrow = self.app.size.width < 60

    def watch_narrow(self, narrow):
        self.set_class(narrow, "stacked")
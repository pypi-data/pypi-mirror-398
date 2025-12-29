from textual.widgets import Static
from rich.text import Text
import plotext

class Plot(Static):
    def create(self):
        return plotext
    
    def on_resize(self):
        self.refresh()
    
    def render(self):
        width = self.size.width
        height = self.size.height  

        plotext.plotsize(width, height)
        output = plotext.build()

        return Text.from_ansi(output)
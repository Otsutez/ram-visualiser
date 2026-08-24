from typing import override

from textual.app import App, ComposeResult, RenderResult
from textual.containers import CenterMiddle, Grid, Vertical
from textual.widget import Widget
from textual.widgets import Footer, Header

"""
           Data
RamReader ------> RamPane
- RamReader parse memory usage from /proc/*

- RamReader returns an easily digestible data to RamePane
- RamPane parses the data and render the ram
"""


class RamView(Widget):
    """Ram widget which will illustrates memory usage"""

    # TODO: Make ram determines it's optimal width and height, dynamically size itself

    background_char: str = "░"

    @override
    def render(self) -> RenderResult:
        result = ""
        for i in range(855):
            code = i % 255
            rendered_char = f"[#ff00{code:02x}]{self.background_char}[/]"
            result += rendered_char
        return result


class RamPane(CenterMiddle):
    @override
    def compose(self) -> ComposeResult:
        yield RamView(id="ram")


class ProcessPane(Vertical):
    pass


class RamVisualiserApp(App):
    CSS_PATH = "app.tcss"
    TITLE = "Ram Visualiser"

    @override
    def compose(self) -> ComposeResult:
        yield Header()
        with Grid(id="grid-pane"):
            yield RamPane(classes="pane")
            yield ProcessPane(classes="pane")
        yield Footer()

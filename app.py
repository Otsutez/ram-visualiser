from typing import override

from textual import log
from textual.app import App, ComposeResult, RenderResult
from textual.containers import CenterMiddle, Grid, Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Footer, Header, Static

"""
           Data
RamReader ------> RamPane

- RamReader parse memory usage from /proc/*
- RamReader returns an easily digestible data to RamePane
- RamPane parses the data and render the ram
"""


class RamReader:
    """
    Gather all processes memory usage and return a rendered string for
    frontend to use
    """

    def get_render(self):
        pass


class Ram(Widget):
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
        yield Ram(id="ram")


class ProcessPane(Vertical):
    pass


class RamVisualiser(App):
    CSS_PATH = "app.tcss"
    TITLE = "Ram Visualiser"

    @override
    def compose(self) -> ComposeResult:
        yield Header()
        with Grid(id="grid-pane"):
            yield RamPane(classes="pane")
            yield ProcessPane(classes="pane")
        yield Footer()


if __name__ == "__main__":
    RamVisualiser().run()

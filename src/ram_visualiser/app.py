from typing import override

from textual.app import App, ComposeResult, RenderResult
from textual.containers import CenterMiddle, Grid, Vertical
from textual.events import Resize
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Footer, Header

"""
           Data
RamReader ------> RamPane
- RamReader parse memory usage from /proc/*

- RamReader returns an easily digestible data to RamPane
- RamPane parses the data and render the ram
"""


class RamView(Widget):
    """Ram widget which will illustrates memory usage"""

    background_char: str = "░"
    min_height: int = 5

    # TODO: Consider if we should not have an inner component but instead draw
    # our ram using a combination of white and dark space

    def calc_new_size(self, parent_height: int, parent_width: int):
        """
        RAM ratio: 1 x 4
        Since a terminal cell's height is roughly twice the width,
        The actual ratio is 1 x 8
        height = width / 8

        We aim to take up 80% of width area, make the width restrict the height,
        unless height will go below min_height, restrict both with parent size

        TODO: Make Ram vertical when screen is a certain size
        """
        width: int = int(parent_width * 0.8)
        height: int = width // 8

        # Restrict height by min_height
        height = max(self.min_height, height)

        # Restrict width and height by parent size
        width = min(parent_width - 2, width)
        height = min(parent_height - 2, height)

        return height, width

    def update_size(self, parent_height: int, parent_width: int):
        new_height, new_width = self.calc_new_size(parent_height, parent_width)
        self.styles.height = new_height
        self.styles.width = new_width
        self.refresh()

        self.log(f"Parent height: {parent_height}")
        self.log(f"Parent width: {parent_width}")
        self.log(f"Ram height: {self.size.height}")
        self.log(f"Ram width: {self.size.width}")

    @override
    def render(self) -> RenderResult:
        return ""
        # result = ""
        # for i in range(855):
        #     code = i % 255
        #     rendered_char = f"[#ff00{code:02x}]{self.background_char}[/]"
        #     result += rendered_char
        # return result


class RamPane(CenterMiddle):
    @override
    def compose(self) -> ComposeResult:
        yield RamView(id="ram")

    def on_resize(self, event: Resize):
        ram_view = self.query_one(RamView)
        ram_view.update_size(self.size.height, self.size.width)


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


if __name__ == "__main__":
    app = RamVisualiserApp()
    app.run()

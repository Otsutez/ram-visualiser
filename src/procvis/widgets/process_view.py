from typing import override

from textual.app import ComposeResult, RenderResult
from textual.containers import CenterMiddle, Grid
from textual.events import Resize
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import TabbedContent, TabPane

"""
Process View Design

Vertical Layout                                                          
┌─────────┌────────┐──────────────┐┌───────────────┐
│ VM      │ Phys   │              ││ Process Info  │
└─────────└────────┘              ││               │
│       ┌──────────────────┐      ││               │
│       │                  │      ││               │
│       │   VM View        │      ││               │
│       │                  │      ││               │
│       │                  │      ││               │
│       │                  │      ││               │
│       │                  │      ││               │
│       │                  │      ││               │
│       │                  │      ││               │
│       │                  │      ││               │
│       │                  │      ││               │
│       │                  │      ││               │
│       │                  │      ││               │
│       └──────────────────┘      ││               │
│                                 ││               │
└─────────────────────────────────┘└───────────────┘
"""


class VMBlock(Widget):
    width: reactive[int] = reactive(0)
    height: reactive[int] = reactive(0)
    BACKGROUND_CHAR: str = "░"

    def watch_width(self, width: int) -> None:
        self.styles.width = width

    def watch_height(self, height: int) -> None:
        self.styles.height = height

    @override
    def render(self) -> RenderResult:
        result = ""
        for r in range(self.height):
            for c in range(self.width):
                rendered_char = f"[#ff0000]{self.BACKGROUND_CHAR}[/]"
                result += rendered_char
        return result


class VMView(CenterMiddle):
    MAX_V_WIDTH: int = 40
    MAX_H_HEIGHT: int = 15
    is_vertical: reactive[int] = reactive(False)

    @override
    def compose(self) -> ComposeResult:
        yield VMBlock()

    def calc_ver_blk_size(self, width: int, height: int) -> tuple[int, int]:
        blk_width = min(self.MAX_V_WIDTH, int(width * 0.8))
        blk_height = int(height * 0.9)
        return blk_width, blk_height

    def calc_hor_blk_size(self, width: int, height: int) -> tuple[int, int]:
        blk_width = int(width * 0.9)
        blk_height = min(self.MAX_H_HEIGHT, int(height * 0.8))
        return blk_width, blk_height

    def on_resize(self, event: Resize) -> None:
        # Recalculate vm block size
        blk_width, blk_height = (
            self.calc_ver_blk_size(event.size.width, event.size.height)
            if self.is_vertical
            else self.calc_hor_blk_size(event.size.width, event.size.height)
        )
        block = self.query_one(VMBlock)
        block.width = blk_width
        block.height = blk_height


class ProcessInfo(Widget):
    pass


class ProcessView(Grid):
    pid: reactive[int] = reactive(0)

    @override
    def compose(self) -> ComposeResult:
        with TabbedContent(id="vm-tabbed-pane", initial="vm"):
            with TabPane("VM", id="vm"):
                yield VMView(id="vm-view")
        yield ProcessInfo(id="process-info")

    def on_resize(self, event: Resize) -> None:
        """When resize occur, calculate optimum layout and switch to it"""
        v_ram_pane_width = int(self.size.width * 0.65)
        v_vm_view_width = int(v_ram_pane_width * 0.8)
        v_vm_view_width = min(VMView.MAX_V_WIDTH, v_vm_view_width)
        v_vm_view_height = int(self.size.height * 0.9)
        v_area = v_vm_view_height * v_vm_view_width

        self.log(f"width: {self.size.width}")
        self.log(f"height: {self.size.height}")
        self.log(f"v_vm_view_width: {v_vm_view_width}")
        self.log(f"v_vm_view_height: {v_vm_view_height}")
        self.log(f"v_area: {v_area}")

        h_ram_pane_height = int(self.size.height * 0.65)
        h_vm_view_height = int(h_ram_pane_height * 0.8)
        v_vm_view_height = min(VMView.MAX_H_HEIGHT, v_vm_view_height)
        h_vm_view_width = int(self.size.width * 0.9)
        h_area = h_vm_view_height * h_vm_view_width

        self.log(f"h_vm_view_width: {h_vm_view_width}")
        self.log(f"h_vm_view_height: {h_vm_view_height}")
        self.log(f"h_area: {h_area}")

        vm_view = self.query_one(VMView)

        if v_area >= h_area:
            if self.has_class("horizontal-grid"):
                self.remove_class("horizontal-grid")
            if not self.has_class("vertical-grid"):
                self.add_class("vertical-grid")
            vm_view.is_vertical = True
        else:
            if self.has_class("vertical-grid"):
                self.remove_class("vertical-grid")
            if not self.has_class("horizontal-grid"):
                self.add_class("horizontal-grid")
            vm_view.is_vertical = False

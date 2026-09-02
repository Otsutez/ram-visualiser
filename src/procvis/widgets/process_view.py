from typing import override

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static

#     def calc_new_size(self, parent_height: int, parent_width: int):
#         """
#         Calculate RamView size based on it's parent size. Adjust Ram to be horizontal
#         or vertical to maximise area
#         """
#         # Calculate vertical size
#         v_height: int = int(parent_height * 0.8)
#         v_width: int = v_height

#         # Calculate horizontal size
#         h_width: int = int(parent_width * 0.8)
#         h_height: int = h_width // 4

#         # Choose orientation that results in largest area
#         v_area = v_width * v_height
#         h_area = h_width * h_height
#         self.log(f"v_area: {v_area}")
#         self.log(f"h_area: {h_area}")
#         if v_area > h_area:
#             width = v_width
#             height = v_height
#         else:
#             width = h_width
#             height = h_height

#         # Restrict width and height by parent size
#         width = min(parent_width - 2, width)
#         height = min(parent_height - 2, height)

#         return height, width

#     def update_size(self, parent_height: int, parent_width: int):
#         new_height, new_width = self.calc_new_size(parent_height, parent_width)
#         self.styles.height = new_height
#         self.styles.width = new_width
#         self.refresh()

#         self.log(f"Parent height: {parent_height}")
#         self.log(f"Parent width: {parent_width}")
#         self.log(f"Ram height: {self.size.height}")
#         self.log(f"Ram width: {self.size.width}")

#     @override
#     def render(self) -> RenderResult:
#         return ""
#         # result = ""
#         # for i in range(855):
#         #     code = i % 255
#         #     rendered_char = f"[#ff00{code:02x}]{self.background_char}[/]"
#         #     result += rendered_char
#         # return result


# class RamPane(CenterMiddle):
#     @override
#     def compose(self) -> ComposeResult:
#         yield RamView(id="ram")

#     def on_resize(self, event: Resize):
#         ram_view = self.query_one(RamView)
#         ram_view.update_size(self.size.height, self.size.width)


class ProcessView(Widget):
    pid: reactive[int] = reactive(0)

    @override
    def compose(self) -> ComposeResult:
        yield Static(f"{self.pid}")

    pass

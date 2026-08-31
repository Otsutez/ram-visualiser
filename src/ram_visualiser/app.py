from typing import override

from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import CenterMiddle
from textual.reactive import reactive
from textual.widgets import DataTable, Footer, Header, ListView

from ram_visualiser.memory_parser import (
    MemoryParser,
    MemoryReader,
    Stat,
)

memory_parser: MemoryParser = MemoryParser()


# class RamView(Static):
#     """Ram widget which will illustrates memory usage"""

#     background_char: str = "░"
#     memory_parser: MemoryParser = MemoryParser()
#     process_map: reactive[dict[int, ProcessData] | None] = reactive(None)

#     def on_mount(self) -> None:
#         self.set_interval(1, self.execute_worker)

#     def execute_worker(self) -> None:
#         worker = self.update_process_map()

#     @work(thread=True)
#     def update_process_map(self):
#         worker = get_current_worker()
#         try:
#             map = self.memory_parser.get_process_map()
#             if not worker.is_cancelled:
#                 self.app.call_from_thread(self.set_process_map, map)
#         except GetProcessMapError as e:
#             self.log(str(e))

#     def set_process_map(self, map: dict[int, ProcessData]):
#         self.process_map = map

#     def on_worker_state_changed(self, event: Worker.StateChanged):
#         self.log(event)

#     def watch_process_map(self, process_map: dict[int, ProcessData] | None):
#         if process_map is None:
#             return

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


class ProcessSelector(DataTable):
    stats: reactive[list[Stat]] = reactive([])
    COLOR_1 = "white"
    COLOR_2 = "green"

    @override
    def on_mount(self) -> None:
        """Add border title and columns"""
        self.border_title: str = "Select a process:"
        _ = self.add_columns("Pid:", "Program:", "Command:", "Threads:", "Mem Usage:")

    def get_styled_row(self, stat: Stat) -> list[Text]:
        return [
            Text(str(stat.pid), style=self.COLOR_1, justify="right"),
            Text(stat.comm[:16], style=self.COLOR_2),
            Text(stat.cmdline[:32], style=self.COLOR_1),
            Text(str(stat.num_threads), style=self.COLOR_2, justify="right"),
            # Text(stat., style=self.COLOR_1)
            Text(
                MemoryReader.format_bytes(stat.rss * MemoryReader.PAGE_SIZE),
                style=self.COLOR_2,
                justify="right",
            ),
        ]

    def watch_stats(self, stats: list[Stat]) -> None:
        """Update rows when process stats update"""
        for stat in stats:
            _ = self.add_row(*self.get_styled_row(stat))

    @override
    def compose(self) -> ComposeResult:
        yield ListView(id="process-list")


class ProcessVisualiserApp(App):
    CSS_PATH = "app.tcss"
    TITLE = "Ram Visualiser"
    stats: reactive[dict[int, Stat]] = reactive({})
    pids: reactive[list[int]] = reactive([])

    def on_mount(self) -> None:
        """Update process information every 5 seconds"""
        self.set_interval(5, self.update_pids)

    def update_pids(self) -> None:
        self.pids = MemoryReader.get_pids()

    def compute_stats(self) -> dict[int, Stat]:
        """Retrieve stats for all pids when pids updated"""
        stats: dict[int, Stat] = {}
        for pid in self.pids:
            stat = MemoryReader.read_stat(pid)
            if stat:
                stats[pid] = stat
            else:
                self.log(f"Error: failed to read stat for process: {pid}")

        return stats

    def watch_stats(self, stats: dict[int, Stat]) -> None:
        selector = self.query_one(ProcessSelector)
        selector.stats = list(stats.values())

    @override
    def compose(self) -> ComposeResult:
        yield Header()
        yield CenterMiddle(ProcessSelector())
        # with Grid(id="grid-pane"):
        #     yield RamPane(classes="pane")
        yield Footer()


if __name__ == "__main__":
    app = ProcessVisualiserApp()
    app.run()

from typing import override

from rich.text import Text
from textual import work
from textual.app import App, ComposeResult
from textual.containers import CenterMiddle
from textual.reactive import reactive
from textual.widgets import DataTable, Footer, Header, ListView
from textual.worker import Worker, get_current_worker

from procvis.memory import (
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

    BINDINGS = [
        ("p", "sort_by_pid", "Sort By Pid"),
        ("r", "sort_by_program", "Sort By Program"),
        ("c", "sort_by_command", "Sort By Command"),
        ("t", "sort_by_threads", "Sort By Threads"),
        ("u", "sort_by_user", "Sort By User"),
        ("m", "sort_by_mem", "Sort By Memory"),
    ]

    current_sort = "mem"

    def action_sort_by_pid(self) -> None:
        self.sort("pid", key=lambda pid: int(pid.plain))
        self.current_sort = "pid"

    def action_sort_by_program(self) -> None:
        self.sort("program", key=lambda prog: prog.plain)
        self.current_sort = "program"

    def action_sort_by_command(self) -> None:
        self.sort("command", key=lambda comm: comm.plain)
        self.current_sort = "command"

    def action_sort_by_threads(self) -> None:
        self.sort("threads", key=lambda threads: int(threads.plain), reverse=True)
        self.current_sort = "threads"

    def action_sort_by_user(self) -> None:
        self.sort("user", key=lambda user: user.plain)
        self.current_sort = "user"

    def action_sort_by_mem(self) -> None:
        self.sort(
            "mem", key=lambda mem: MemoryReader.unformat_bytes(mem.plain), reverse=True
        )
        self.current_sort = "mem"

    @override
    def on_mount(self) -> None:
        """Add border title and columns"""
        self.border_title: str = "Select a process:"
        _ = self.add_columns(
            ("Pid:", "pid"),
            ("Program:", "program"),
            ("Command:", "command"),
            ("Threads:", "threads"),
            ("User:", "user"),
            ("Mem:", "mem"),
        )
        self.cursor_type = "row"

    def get_styled_row(self, stat: Stat) -> list[Text]:
        return [
            Text(str(stat.pid), style=self.COLOR_1, justify="right"),
            Text(stat.comm[:16], style=self.COLOR_2),
            Text(stat.cmdline[:32], style=self.COLOR_1),
            Text(str(stat.num_threads), style=self.COLOR_2, justify="right"),
            Text(stat.user[:10], style=self.COLOR_1),
            Text(
                MemoryReader.format_bytes(stat.rss * MemoryReader.PAGE_SIZE),
                style=self.COLOR_2,
                justify="right",
            ),
        ]

    def watch_stats(self, stats: list[Stat]) -> None:
        """Update rows when process stats update"""
        self.clear()
        for stat in stats:
            _ = self.add_row(*self.get_styled_row(stat))

        # Sort into previous order
        if self.current_sort == "pid":
            self.action_sort_by_pid()
        elif self.current_sort == "program":
            self.action_sort_by_program()
        elif self.current_sort == "command":
            self.action_sort_by_command()
        elif self.current_sort == "threads":
            self.action_sort_by_threads()
        elif self.current_sort == "user":
            self.action_sort_by_user()
        elif self.current_sort == "mem":
            self.action_sort_by_mem()

    @override
    def compose(self) -> ComposeResult:
        yield ListView(id="process-list")


class ProcessVisualiserApp(App):
    CSS_PATH = "app.tcss"
    TITLE = "Ram Visualiser"
    stats: reactive[dict[int, Stat]] = reactive({})
    pids: reactive[list[int]] = reactive([])

    def on_mount(self) -> None:
        """Start worker to fetch pids"""
        self.update_pids()
        self.set_interval(5, self.update_pids)

    @work(exclusive=True, thread=True)
    def update_pids(self) -> None:
        worker = get_current_worker()
        pids = MemoryReader.get_pids()
        if not worker.is_cancelled:
            self.call_from_thread(self.set_pids, pids)

    def set_pids(self, pids: list[int]) -> None:
        self.pids = pids

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        self.log(event)

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
        yield Footer()


if __name__ == "__main__":
    app = ProcessVisualiserApp()
    app.run()

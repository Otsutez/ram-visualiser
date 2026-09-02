from typing import override

from textual import work
from textual.app import App, ComposeResult
from textual.containers import CenterMiddle
from textual.reactive import reactive
from textual.widgets import ContentSwitcher, Footer, Header
from textual.worker import Worker, get_current_worker

from procvis.memory import (
    MemoryReader,
    Stat,
)
from procvis.widgets import ProcessSelector, ProcessView


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
        with ContentSwitcher(initial="process-selector"):
            with CenterMiddle(id="process-selector"):
                yield ProcessSelector()
            yield ProcessView(id="process-view")
        yield Footer()

    def on_process_selector_selected(self, event: ProcessSelector.Selected):
        if event.pid is not None:
            self.query_one(ProcessView).pid = event.pid
            self.query_one(ContentSwitcher).current = "process-view"
            self.log(f"{event.pid} selected")


if __name__ == "__main__":
    app = ProcessVisualiserApp()
    app.run()

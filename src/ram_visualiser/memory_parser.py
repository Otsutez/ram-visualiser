import os
import re
import subprocess
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path


class GetProcessMapError(Exception):
    """Raised when memory_parser failed to retrieve process data"""

    pass


@dataclass
class Stat:
    pid: int
    comm: str
    cmdline: str
    state: str
    ppid: int
    pgrp: int
    session: int
    tty_nr: int
    tpgid: int
    flags: int
    minflt: int
    cminflt: int
    majflt: int
    cmajflt: int
    utime: int
    stime: int
    cutime: int
    cstime: int
    priority: int
    nice: int
    num_threads: int
    itrealvalue: int
    starttime: int
    vsize: int
    rss: int
    rsslim: int
    startcode: int
    endcode: int
    startstack: int
    kstkesp: int
    kstkeip: int
    signal: int
    blocked: int
    sigignore: int
    sigcatch: int
    wchan: int
    nswap: int
    cnswap: int
    exit_signal: int
    processor: int
    rt_priority: int
    policy: int
    delayacct_blkio_ticks: int
    guest_time: int
    cguest_time: int
    start_data: int
    end_data: int
    start_brk: int
    arg_start: int
    arg_end: int
    env_start: int
    env_end: int
    exit_code: int


@dataclass
class PageMapEntry:
    pfn: int
    soft_dirty: bool
    file_page: bool
    swapped: bool
    present: bool


@dataclass
class MapsEntry:
    address: tuple[int, int]
    perms: str
    offset: int
    dev: str
    inode: int
    pathname: str


@dataclass
class ProcessData:
    name: str
    maps_entries: list[MapsEntry]
    pagemap_entries: dict[int, PageMapEntry]


def read_cmdline(pid: int) -> str:
    cmdline_file = Path(f"/proc/{pid}/cmdline")
    try:
        with cmdline_file.open("r") as c:
            return c.read().strip()
    except OSError:
        return ""


def read_stat(pid: int) -> Stat | None:
    cmdline = read_cmdline(pid)
    stat_file = Path(f"/proc/{pid}/stat")
    try:
        with stat_file.open("r") as s:
            stat = s.read().strip()

            # Parse stat
            if match := re.match(
                r"^.*\((?P<comm>[^\)]*)\)\s(?P<state>[RSDZTtWXxKWPI])\s(?P<rest>.*)$",
                stat,
            ):
                comm = match.group("comm")
                state = match.group("state")
                rest = map(int, match.group("rest").split())
                return Stat(pid, comm, cmdline, state, *rest)
            else:
                # Return None if format of stat file does not match our expectations
                return None
    except (OSError, ValueError):
        return None


def get_all_stats() -> list[Stat]:
    proc_dir = Path("/proc")
    pids = [int(file) for file in os.listdir(proc_dir) if file.isdigit()]
    result: list[Stat] = []
    for pid in pids:
        stat = read_stat(pid)
        if stat:
            result.append(stat)
    return result


class MemoryParser:
    """
    Gather all processes memory usage and return concise data for RamView to
    interpret and render
    """

    def __init__(self):
        self.lines: Iterator[str] | None = None
        self.curr: str | None = None

    def accept(self):
        if self.lines is None:
            return
        try:
            self.curr = next(self.lines)
        except StopIteration:
            self.curr = None

    def get_process_name(self, pid: int) -> str:
        path = Path(f"/proc/{pid}/comm")
        try:
            with path.open() as f:
                return f.read().strip()
        except (FileNotFoundError, PermissionError, OSError):
            return ""

    def parse_pagemap_entry(self) -> tuple[int, PageMapEntry] | None:
        if self.curr is None:
            return None

        pattern = re.compile(
            r"""
            ^
            (?P<vaddr>[0-9a-f]+)\s # virtual address
            (?P<pfn>[0-9a-f]+)\s   # page frame number
            (?P<soft>[01])\s       # soft dirty bit
            (?P<filepage>[01])\s   # file page bit
            (?P<swapped>[01])\s    # swapped bit
            (?P<present>[01])    # present bit
            $
            """,
            re.VERBOSE,
        )

        if match := pattern.match(self.curr):
            self.accept()
            groups = match.groupdict()
            vaddr = int(groups["vaddr"], 16)
            pfn = int(groups["pfn"], 16)
            soft = groups["soft"] == "1"
            filepage = groups["filepage"] == "1"
            swapped = groups["swapped"] == "1"
            present = groups["present"] == "1"

            pagemap_entry = PageMapEntry(
                pfn=pfn,
                soft_dirty=soft,
                file_page=filepage,
                swapped=swapped,
                present=present,
            )
            return (vaddr, pagemap_entry)

    def parse_maps_entry(self) -> MapsEntry | None:
        if self.curr is None:
            return None

        # Regular expression to match maps entry
        pattern = re.compile(
            r"""
            ^
            (?P<addr1>[0-9a-f]+)-        # first address
            (?P<addr2>[0-9a-f]+)\s       # second address
            (?P<perms>[r\-][w\-][x\-][s\-p])\s # permissions
            (?P<offset>\d+)\s               # offset
            (?P<dev>\d+:\d+)\s              # device
            (?P<inode>\d+)\s+               # inode
            (?P<pathname>.*)                # pathname
            $
            """,
            re.VERBOSE,
        )
        if match := pattern.match(self.curr):
            self.accept()
            groups = match.groupdict()
            addr1 = int(groups["addr1"], 16)
            addr2 = int(groups["addr2"], 16)
            perms = groups["perms"]
            offset = int(groups["offset"])
            dev = groups["dev"]
            inode = int(groups["inode"])
            pathname = groups["pathname"]

            return MapsEntry(
                address=(addr1, addr2),
                perms=perms,
                offset=offset,
                dev=dev,
                inode=inode,
                pathname=pathname,
            )

        return None

    def parse_pid(self) -> int | None:
        if self.curr is None:
            return None

        if self.curr.isdigit():
            pid = int(self.curr, 10)
            self.accept()
            return pid

    def parse_output(self, output: str) -> dict[int, ProcessData]:
        """
        Grammar:
        output = proc_data
        proc_data = pid data*
        data = maps_entry pagemap_entry*
        """
        # Prepare iterator
        self.lines = iter(output.splitlines())
        self.accept()

        map: dict[int, ProcessData] = {}
        while (pid := self.parse_pid()) is not None:
            maps_entries: list[MapsEntry] = []
            pagemap_entries: dict[int, PageMapEntry] = {}
            name = self.get_process_name(pid)

            while (maps_entry := self.parse_maps_entry()) is not None:
                maps_entries.append(maps_entry)
                while (data := self.parse_pagemap_entry()) is not None:
                    vaddr, pagemap_entry = data
                    pagemap_entries[vaddr] = pagemap_entry
            map[pid] = ProcessData(
                name=name, maps_entries=maps_entries, pagemap_entries=pagemap_entries
            )
        return map

    def get_pids(self) -> list[int]:
        proc_dir = Path("/proc")
        pids = [int(file) for file in os.listdir(proc_dir) if file.isdigit()]
        return pids

    def get_pids_str(self) -> str:
        pids = self.get_pids()
        pids = "\n".join(map(str, pids))
        return pids

    def run_reader(self, pids: str) -> str:
        process = subprocess.run(
            ["build/bin/reader"],
            input=pids,
            capture_output=True,
            text=True,
            check=True,
        )
        return process.stdout

    def get_process_map(self) -> dict[int, ProcessData]:
        """
        Returns a dictionary of pids mapped to it's memory data.
        Raise GetProcessMapError when failed to get input
        """
        pids = self.get_pids_str()
        print(pids)
        try:
            output = self.run_reader(pids)
        except subprocess.CalledProcessError as e:
            exception = GetProcessMapError(e.stderr)
            raise exception
        map = self.parse_output(output)
        return map


if __name__ == "__main__":
    proc_map = MemoryParser().get_process_map()
    print(map)

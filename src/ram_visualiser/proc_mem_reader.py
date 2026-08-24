import math
import struct
import os
from pathlib import Path


class ProcMemReader:
    """
    Gather all processes memory usage and return concise data for RamView to
    interpret and render
    """

    PAGEMAP_ENTRY_SIZE: int = 8
    PFN_MASK: int = 0x3FFFFFFFFFFFFF
    PRESENT_MASK: int = 2**63

    def __init__(self):
        """Calculate various constants about the system"""
        self.WORD_SIZE: int = struct.calcsize("P") * 8
        self.MAX_VADDR: int = 2**self.WORD_SIZE - 1
        self.PAGE_SIZE: int = os.sysconf("SC_PAGESIZE")
        self.OFFSET_LENGTH: int = int(math.log2(self.PAGE_SIZE))

        mask = self.MAX_VADDR
        mask = mask >> self.OFFSET_LENGTH
        self.VPN_MASK: int = mask << self.OFFSET_LENGTH

    def is_valid_vaddr(self, vaddr: int) -> bool:
        return vaddr >= 0 and vaddr <= self.MAX_VADDR

    def get_range(self, line: str) -> str | None:
        """
        Returns:
            "addr-addr" string if line is in the correct maps format, otherwise returns None
        """
        line = line.strip()
        separated = line.split(" ", 1)
        if len(separated) != 2:
            return None
        return separated[0]

    def get_vaddr_range(self, line: str) -> tuple[int, int] | None:
        range = self.get_range(line)
        if range is None:
            return None

        separated = range.split("-", 1)
        if len(separated) != 2:
            return None
        try:
            low = int(separated[0], 16)
            high = int(separated[1], 16)
        except ValueError:
            return None

        if not self.is_valid_vaddr(low) or not self.is_valid_vaddr(high):
            return None

        return low, high

    def read_vaddr_ranges(self, pid: int) -> list[tuple[int, int]] | None:
        """Read a process maps file and return a list of tuple virtual address ranges mapped by the process

        Args:
            maps_file: path to the process's map file

        Returns:
            A list of virtual address range (tuple) mapped by the process
            Return None if the process virtual address information cannot be retrieved
        """
        maps_file = Path(f"/proc/{pid}/maps")
        if not maps_file.exists():
            return None

        vaddr_ranges: list[tuple[int, int]] = []
        try:
            with maps_file.open() as f:
                for line in f:
                    res = self.get_vaddr_range(line)
                    if res is not None:
                        vaddr_ranges.append(res)
        except (PermissionError, OSError):
            return None

        return vaddr_ranges

    def read_pfns(self, pid: int, vaddr_ranges: list[tuple[int, int]]) -> list[int]:
        """Read PFNs given VPNs and pid from pagemap file
        Args:
            pid: the process id integer
            vpn: the virtual page number integer

        Returns:
            None if failed to open pagemap file, or failed to read pfn using vpn as index, or the page requested was not present in RAM.
        """
        pagemap = Path(f"/proc/{pid}/pagemap")
        pfns: list[int] = []
        if not pagemap.exists():
            return pfns

        try:
            with pagemap.open("rb") as f:
                for low_vaddr, high_vaddr in vaddr_ranges:
                    low_vpn = (low_vaddr & self.VPN_MASK) >> 12
                    high_vpn = (high_vaddr & self.VPN_MASK) >> 12
                    for vpn in range(low_vpn, high_vpn, self.PAGE_SIZE):
                        offset = vpn * ProcMemReader.PAGEMAP_ENTRY_SIZE
                        f.seek(offset)
                        data = int.from_bytes(f.read(ProcMemReader.PAGEMAP_ENTRY_SIZE))
                        pfn = data & ProcMemReader.PFN_MASK
                        present = data & ProcMemReader.PRESENT_MASK
                        if present != 0:
                            pfns.append(pfn)
        except (PermissionError, OSError):
            return pfns

        return pfns

    def get_paddr_map(self) -> dict[int, list[int]]:
        """Get all physical frame numbers mapped to all accessible process in the system

        Returns:
            a dictionary of all accessible pids as keys and list of frames mapped to that pid

        TODO: Return name as well, use json
        TODO: Figure out how to run uv with sudo privilege
        """
        proc_dir = Path("/proc")
        pids = [file for file in os.listdir(proc_dir) if file.isdigit()]
        print(pids)
        res: dict[int, list[int]] = {}
        for pid in pids:
            pid = int(pid)
            vaddr_ranges = self.read_vaddr_ranges(pid)
            if vaddr_ranges is None:
                continue

            pfns = self.read_pfns(pid, vaddr_ranges)
            res[pid] = pfns
        return res


if __name__ == "__main__":
    res = ProcMemReader().get_paddr_map()
    for pid, pfns in res.items():
        print(f"Process: {pid}")
        for pfn in pfns:
            print(f"{pfn:014x}")

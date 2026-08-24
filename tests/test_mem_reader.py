import os

from ram_visualiser.proc_mem_reader import ProcMemReader


class TestGetRange:
    def test_success_case(self):
        test_str = "7ffc94ee5000-7ffc94ee6000 rw-p 00000000 00:00 0 "
        res = ProcMemReader().get_range(test_str)
        assert res == "7ffc94ee5000-7ffc94ee6000"

    def test_failed_case_1(self):
        test_str = "invalid-string"
        res = ProcMemReader().get_range(test_str)
        assert res == None

    def test_failed_case_2(self):
        test_str = "7ffc94ee5000-7ffc94ee6000rw-p0000000000:000 "
        res = ProcMemReader().get_range(test_str)
        assert res == None


# class TestReadVaddrRanges:
#     def test_success_case_1(self):
#         pid = os.getpid()
#         res = ProcMemReader().read_vaddr_ranges(pid)
#         if res is not None:
#             print(res)


class TestGetPaddrMap:
    def test_success(self):
        res = ProcMemReader().get_paddr_map()
        for pid, pfns in res.items():
            print(f"Process: {pid}")
            for pfn in pfns:
                print(f"{pfn:014x}")

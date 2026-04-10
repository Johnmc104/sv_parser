"""
RTL file discovery utilities.

Recursively finds Verilog/SystemVerilog files, with optional
testbench exclusion.
"""

import os
from typing import List


RTL_EXTENSIONS = {".v", ".sv", ".vh", ".svh"}

# Patterns that suggest a file is a testbench
TB_PATTERNS = {"_tb", "testbench", "tb_", "test_", "_test"}


def discover_rtl_files(directory, exclude_tb=True):
    # type: (str, bool) -> List[str]
    """Recursively find Verilog/SV files in *directory*.

    If *exclude_tb* is True, files whose base name contains typical
    testbench patterns are excluded.
    """
    rtl_files = []  # type: List[str]
    for root, _dirs, files in os.walk(directory):
        for f in sorted(files):
            ext = os.path.splitext(f)[1].lower()
            if ext not in RTL_EXTENSIONS:
                continue
            if exclude_tb:
                lower = f.lower()
                if any(p in lower for p in TB_PATTERNS):
                    continue
            rtl_files.append(os.path.join(root, f))
    return rtl_files

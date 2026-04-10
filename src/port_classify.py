"""
Port classification by naming convention.

Provides enums and regex-based classification for clock, reset, DFT,
interrupt, and data ports.
"""

import re
from enum import Enum


class PortDirection(Enum):
    INPUT = "input"
    OUTPUT = "output"
    INOUT = "inout"


class PortCategory(Enum):
    """Port classification for SDC / constraint generation."""
    CLOCK = "clock"
    RESET = "reset"
    DFT = "dft"
    INTERRUPT = "interrupt"
    DATA = "data"


# ---------------------------------------------------------------------------
# Classification regex patterns
# ---------------------------------------------------------------------------

_CLK_RE = re.compile(
    r'(^|_)(clk|clock|pclk|hclk|aclk|fclk|tck|sclk|mclk|gclk|rclk)($|_|\d)',
    re.IGNORECASE,
)
_RST_RE = re.compile(
    r'(^|_)(rst|reset|presetn|hresetn|aresetn)($|_|n\b)',
    re.IGNORECASE,
)
_DFT_RE = re.compile(
    r'(^|_)(scan|dft|jtag|tms|tdi|tdo|trst|bist|mbist)($|_)',
    re.IGNORECASE,
)
_IRQ_RE = re.compile(
    r'(^|_)(intr|irq|interrupt)($|_)|int_req',
    re.IGNORECASE,
)


def classify_port(name):
    """Classify a port by naming convention."""
    if _CLK_RE.search(name):
        return PortCategory.CLOCK
    if _RST_RE.search(name):
        return PortCategory.RESET
    if _DFT_RE.search(name):
        return PortCategory.DFT
    if _IRQ_RE.search(name):
        return PortCategory.INTERRUPT
    return PortCategory.DATA


def detect_reset_active_low(name):
    """True if the reset signal is active-low (ends with _n / n)."""
    return bool(re.search(r'(_n|resetn|rstn)$', name, re.IGNORECASE))

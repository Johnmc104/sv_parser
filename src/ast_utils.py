"""
ANTLR AST utility functions for Verilog parsing.

Provides range evaluation and width calculation helpers.
"""

import re
from typing import Optional, Tuple


def try_eval_range(expr_text):
    # type: (str) -> Optional[int]
    """Try to evaluate a constant range expression to an integer.

    Handles: plain numbers, PARAM-1 style, simple arithmetic.
    Returns None if evaluation fails (parameterized width kept as text).
    """
    text = expr_text.strip()
    if not text:
        return None
    if text.isdigit():
        return int(text)
    # Simple arithmetic with only digits and +-*/
    safe = re.sub(r"[0-9+\-*/() ]", "", text)
    if not safe:
        try:
            return int(eval(text))  # safe: only digits and arithmetic ops
        except Exception:
            pass
    return None


def range_width(range_ctx):
    # type: (...) -> Tuple[int, str]
    """Extract width and range_spec from a range_ context.

    Returns (width, range_text).
    """
    if range_ctx is None:
        return 1, ""

    range_text = range_ctx.getText()
    msb_ctx = range_ctx.msb_constant_expression()
    lsb_ctx = range_ctx.lsb_constant_expression()

    if msb_ctx is None or lsb_ctx is None:
        return 1, range_text

    msb_val = try_eval_range(msb_ctx.getText())
    lsb_val = try_eval_range(lsb_ctx.getText())

    if msb_val is not None and lsb_val is not None:
        width = abs(msb_val - lsb_val) + 1
    else:
        width = 0  # parameterized — can't compute statically

    return width, range_text

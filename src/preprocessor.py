"""
Verilog/SystemVerilog text-level preprocessor.

Handles:
  - `define / `undef         macro definition and removal
  - `ifdef / `ifndef / `elsif / `else / `endif   conditional compilation
  - `include                 file inclusion
  - macro usage (`MACRO_NAME) text expansion

Runs as a pure text transformation BEFORE ANTLR lexing/parsing.
"""

import os
import re
from typing import Dict, List, Optional, Set, Tuple


class PreprocessorError(Exception):
    """Preprocessor error with file/line context."""
    def __init__(self, message: str, file: str = "", line: int = 0):
        self.file = file
        self.line = line
        super().__init__(f"{file}:{line}: {message}" if file else message)


class Preprocessor:
    """
    Verilog/SystemVerilog text-level preprocessor.

    Usage::

        pp = Preprocessor()
        pp.add_define("SYNTHESIS")
        pp.add_include_dir("/path/to/includes")
        result = pp.process_file("top.v")
        # or
        result = pp.process_text(source_text, filename="top.v")
    """

    def __init__(self):
        self._macros: Dict[str, str] = {}
        self._include_dirs: List[str] = []
        self._included_files: Set[str] = set()  # guard against circular include
        self._max_include_depth = 64

    # ---- public configuration ----

    def add_define(self, name: str, value: str = ""):
        """Add a macro definition (like +define+NAME=VALUE)."""
        self._macros[name] = value

    def add_defines(self, defines: Dict[str, str]):
        """Add multiple macro definitions."""
        self._macros.update(defines)

    def add_include_dir(self, path: str):
        """Add an include search directory."""
        if path not in self._include_dirs:
            self._include_dirs.append(path)

    def add_include_dirs(self, dirs: List[str]):
        for d in dirs:
            self.add_include_dir(d)

    @property
    def macros(self) -> Dict[str, str]:
        """Current macro definitions (read-only copy)."""
        return dict(self._macros)

    # ---- main API ----

    def process_file(self, filepath: str) -> str:
        """Preprocess a Verilog file.  Returns preprocessed text."""
        filepath = os.path.abspath(filepath)
        if not os.path.isfile(filepath):
            raise PreprocessorError(f"File not found: {filepath}")

        file_dir = os.path.dirname(filepath)
        if file_dir not in self._include_dirs:
            self._include_dirs.insert(0, file_dir)

        with open(filepath, "r", errors="replace") as f:
            text = f.read()

        return self._process(text, filepath, depth=0)

    def process_text(self, text: str, filename: str = "<string>") -> str:
        """Preprocess a Verilog text string."""
        return self._process(text, filename, depth=0)

    # ---- regex patterns ----

    _RE_UNDEF = re.compile(r"`undef\s+(\w+)")
    _RE_INCLUDE = re.compile(r'`include\s+"([^"]+)"')
    _RE_INCLUDE_ANGLE = re.compile(r"`include\s+<([^>]+)>")
    _RE_MACRO_USAGE = re.compile(r"`(\w+)")

    _PASSTHROUGH_DIRECTIVES = frozenset({
        "timescale", "resetall", "default_nettype",
        "celldefine", "endcelldefine",
    })

    _KNOWN_DIRECTIVES = frozenset({
        "define", "undef", "ifdef", "ifndef", "elsif", "else", "endif",
        "include", "timescale", "resetall", "default_nettype",
        "celldefine", "endcelldefine", "pragma", "line",
        "begin_keywords", "end_keywords",
        "unconnected_drive", "nounconnected_drive",
    })

    # ---- internal implementation ----

    def _process(self, text: str, filename: str, depth: int) -> str:
        if depth > self._max_include_depth:
            raise PreprocessorError(
                f"Maximum include depth ({self._max_include_depth}) exceeded",
                filename,
            )

        lines = text.split("\n")
        output: List[str] = []
        i = 0

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # `define (possibly multiline)
            if stripped.startswith("`define"):
                i = self._handle_define(lines, i)
                output.append("")
                continue

            # `undef
            if stripped.startswith("`undef"):
                m = self._RE_UNDEF.search(stripped)
                if m:
                    self._macros.pop(m.group(1), None)
                output.append("")
                i += 1
                continue

            # `ifdef / `ifndef
            if stripped.startswith("`ifdef") or stripped.startswith("`ifndef"):
                block, i = self._handle_conditional(lines, i, filename)
                output.extend(block)
                continue

            # `include
            if stripped.startswith("`include"):
                inc = self._handle_include(stripped, filename, depth)
                output.extend(inc)
                i += 1
                continue

            # passthrough → strip
            if any(stripped.startswith(f"`{d}") for d in self._PASSTHROUGH_DIRECTIVES):
                output.append("")
                i += 1
                continue

            # expand macros in ordinary lines
            output.append(self._expand_macros(line))
            i += 1

        return "\n".join(output)

    def _handle_define(self, lines: List[str], start: int) -> int:
        combined = lines[start]
        i = start
        while combined.rstrip().endswith("\\") and i + 1 < len(lines):
            i += 1
            combined = combined.rstrip()[:-1] + " " + lines[i]

        rest = combined.strip()[len("`define"):].strip()
        m = re.match(r"(\w+)(?:\s+(.*))?$", rest, re.DOTALL)
        if m:
            self._macros[m.group(1)] = (m.group(2) or "").strip()
        return i + 1

    def _handle_conditional(
        self, lines: List[str], start: int, filename: str
    ) -> Tuple[List[str], int]:
        stripped = lines[start].strip()

        if stripped.startswith("`ifdef"):
            macro = stripped[len("`ifdef"):].strip().split()[0] if stripped[len("`ifdef"):].strip() else ""
            cond = macro in self._macros
        else:  # `ifndef
            macro = stripped[len("`ifndef"):].strip().split()[0] if stripped[len("`ifndef"):].strip() else ""
            cond = macro not in self._macros

        branches: List[Tuple[bool, List[str]]] = []
        cur_lines: List[str] = []
        cur_cond = cond
        nesting = 0
        i = start + 1

        while i < len(lines):
            s = lines[i].strip()

            if s.startswith("`ifdef") or s.startswith("`ifndef"):
                nesting += 1
                cur_lines.append(lines[i])
                i += 1
                continue

            if nesting > 0:
                if s.startswith("`endif"):
                    nesting -= 1
                cur_lines.append(lines[i])
                i += 1
                continue

            if s.startswith("`elsif"):
                branches.append((cur_cond, cur_lines))
                cur_lines = []
                m = s[len("`elsif"):].strip().split()[0] if s[len("`elsif"):].strip() else ""
                cur_cond = m in self._macros
                i += 1
                continue

            if s.startswith("`else"):
                branches.append((cur_cond, cur_lines))
                cur_lines = []
                cur_cond = True
                i += 1
                continue

            if s.startswith("`endif"):
                branches.append((cur_cond, cur_lines))
                i += 1
                break

            cur_lines.append(lines[i])
            i += 1
        else:
            raise PreprocessorError(
                "Unterminated `ifdef/`ifndef block", filename, start + 1
            )

        selected: List[str] = []
        done = False
        for c, bl in branches:
            if c and not done:
                text = "\n".join(bl)
                selected = self._process(text, filename, depth=0).split("\n")
                done = True

        total = i - start
        while len(selected) < total:
            selected.append("")
        return selected[:total], i

    def _handle_include(
        self, line: str, filename: str, depth: int
    ) -> List[str]:
        m = self._RE_INCLUDE.search(line) or self._RE_INCLUDE_ANGLE.search(line)
        if not m:
            return [""]

        inc_name = m.group(1)
        inc_path = self._resolve_include(inc_name, filename)

        if inc_path is None:
            return [f"// [preprocessor] include not found: {inc_name}"]

        abs_path = os.path.abspath(inc_path)
        if abs_path in self._included_files:
            return [f"// [preprocessor] already included: {inc_name}"]
        self._included_files.add(abs_path)

        with open(inc_path, "r", errors="replace") as f:
            inc_text = f.read()

        return self._process(inc_text, inc_path, depth + 1).split("\n")

    def _resolve_include(
        self, inc_name: str, current_file: str
    ) -> Optional[str]:
        cur_dir = os.path.dirname(os.path.abspath(current_file))
        candidate = os.path.join(cur_dir, inc_name)
        if os.path.isfile(candidate):
            return candidate

        for d in self._include_dirs:
            candidate = os.path.join(d, inc_name)
            if os.path.isfile(candidate):
                return candidate
        return None

    def _expand_macros(self, line: str) -> str:
        if "//" in line:
            idx = line.index("//")
            return self._expand_in_code(line[:idx]) + line[idx:]
        return self._expand_in_code(line)

    def _expand_in_code(self, text: str) -> str:
        def _repl(m):
            name = m.group(1)
            if name in self._KNOWN_DIRECTIVES:
                return m.group(0)
            if name in self._macros:
                return self._macros[name]
            return m.group(0)

        return self._RE_MACRO_USAGE.sub(_repl, text)

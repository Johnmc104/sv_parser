# rtl_scan

Verilog/SystemVerilog RTL structure analysis tool. Parses RTL source files and extracts module declarations, port information, hierarchy, and generates instantiation templates.

## Features

- **Module extraction** — ports, parameters, instances, wires from Verilog-2005
- **Hierarchy analysis** — dependency graph, top module detection, unresolved references
- **Port classification** — clock, reset, DFT, interrupt, data (by naming convention)
- **Filelist generation** — bottom-up compilation order
- **Instantiation template** — `.port(w_signal)` style with wire declarations
- **Port I/O table** — tabular port summary with width and direction
- **Preprocessor** — \`define, \`ifdef/\`ifndef, \`include, macro expansion

## Requirements

- Python >= 3.6
- `antlr4-python3-runtime == 4.13.1`
- Java (OpenJDK 1.8+) — only for regenerating ANTLR grammars

## Installation

```bash
pip install antlr4-python3-runtime==4.13.1
```

## Usage

### CLI

```bash
# Scan a directory (full analysis)
python -m src ./rtl

# Scan a single file
python -m src top.v -m inst          # instantiation template
python -m src top.v -m io            # port I/O table
python -m src top.v -m ports         # port classification

# Scan from filelist
python -m src -f filelist.f -m hierarchy -t top_chip

# Output options
python -m src ./rtl -o result.json   # JSON file
python -m src ./rtl -j               # JSON stdout
python -m src ./rtl -v               # verbose logging
python -m src ./rtl -vv              # debug logging

# Preprocessor options
python -m src ./rtl -D SYNTHESIS -D USE_PLL=1 -I ./inc
```

### Modes

| Mode | Description |
|------|-------------|
| `full` | All analysis (default) |
| `modules` | Module declarations only |
| `hierarchy` | Modules + dependency tree |
| `ports` | Modules + port classification |
| `filelist` | Full analysis + compilation filelist |
| `inst` | Instantiation template |
| `io` | Port I/O table |

### Python API

```python
from src.rtl_scan import rtl_scan, rtl_scan_json

# Scan directory
result = rtl_scan(directory="./rtl", mode="full")

# Scan single file
result = rtl_scan(file="top.v", mode="inst")

# Scan file list
result = rtl_scan(files=["a.v", "b.v"], mode="modules")

# JSON output
json_str = rtl_scan_json(directory="./rtl")
```

## Build Binary

```bash
# Local build (requires PyInstaller)
make build-local

# Docker build (CentOS 7 / glibc 2.17 compatible)
make build
```

## ANTLR Grammar Regeneration

```bash
make gen       # regenerate Verilog parser from .g4 grammars
```

Requires Java (OpenJDK 1.8+) and the ANTLR jar in `antlr/`.

## Testing

```bash
python -m pytest test/ -v
```

## Project Structure

```
src/                  # Main source package
  __main__.py         # CLI entry point
  rtl_scan.py         # Top-level API
  verilog_parser.py   # ANTLR parser → ModuleInfo
  preprocessor.py     # `define/`ifdef/`include
  data_model.py       # Dataclass models
  formatter.py        # Terminal output formatters
  hierarchy.py        # Dependency analysis
  file_discovery.py   # RTL file finder
  extractors.py       # ANTLR AST extraction
  port_classify.py    # Port classification
  ast_utils.py        # Range evaluation
  log.py              # Logging configuration
verilog/              # ANTLR generated Verilog-2005 grammar
systemverilog/        # ANTLR generated SystemVerilog grammar
packaging/            # Docker + PyInstaller build
test/                 # pytest test suite
  fixtures/           # Test data files
```
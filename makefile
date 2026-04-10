#need java11
language=verilog
antlr_version=4.13.1
export CLASSPATH=/home/zhhe/work/sv_parser/antlr/antlr-${antlr_version}-complete.jar

antlr4=java -cp antlr/antlr-${antlr_version}-complete.jar org.antlr.v4.Tool

systemverilog= \
	systemverilog/SystemVerilogLexer.g4 \
	systemverilog/SystemVerilogParser.g4 \
	systemverilog/SystemVerilogPreParser.g4

verilog= \
	verilog/VerilogLexer.g4 \
	verilog/VerilogParser.g4 \
	verilog/VerilogPreParser.g4

ifeq (${language}, systemverilog)
language_lib=${systemverilog}
else ifeq (${language}, verilog)
language_lib=${verilog}
endif

.DEFAULT_GOAL := help

# ---- ANTLR ----

.PHONY: gen python-deps test-antlr

python-deps:
	pip3 install antlr4-python3-runtime==${antlr_version}

test-antlr:
	java org.antlr.v4.Tool

gen:
	${antlr4} -no-listener -visitor -Dlanguage=Python3 ${language_lib}

# ---- build ----

.PHONY: build build-local

build:
	./packaging/build.sh

build-local:
	./packaging/build.sh --local

# ---- dev ----

.PHONY: run test install

run:
	@python3 -m src $(ARGS)

test:
	python3 test/test_gpio.py
	python3 test/test_multi.py
	python3 test/test_rtl_scan.py

install:
	@test -f dist/rtl_scan || { echo "run make build or make build-local first"; exit 1; }
	@cp -v dist/rtl_scan /usr/local/bin/rtl_scan 2>/dev/null || \
	 cp -v dist/rtl_scan $$HOME/.local/bin/rtl_scan
	@echo "Installed: $$(which rtl_scan 2>/dev/null || echo $$HOME/.local/bin/rtl_scan)"

# ---- clean ----

.PHONY: clean clean-build

clean-build:
	rm -rf dist/ build/

clean: clean-build
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# ---- help ----

.PHONY: help

help:
	@echo "rtl_scan Makefile"
	@echo ""
	@echo "Build:"
	@echo "  make build        Docker build (CentOS 7 / glibc 2.17)"
	@echo "  make build-local  Local build (current glibc only)"
	@echo "  make install      Install binary to system"
	@echo ""
	@echo "ANTLR:"
	@echo "  make gen          Generate Python visitors from g4"
	@echo "  make python-deps  Install ANTLR Python runtime"
	@echo ""
	@echo "Dev:"
	@echo "  make run ARGS=\"./rtl\"  Run in dev mode"
	@echo "  make test         Run tests"
	@echo ""
	@echo "Clean:"
	@echo "  make clean-build  Remove dist/ build/"
	@echo "  make clean        Remove all generated files"

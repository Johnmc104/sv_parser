#need java11
language=verilog
antlr_version=4.13.1
export CLASSPATH=/home/zhhe/work/sv_parser/antlr/antlr-${antlr_version}-complete.jar

#antlr4=java -jar antlr/antlr-4.8-complete.jar
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

# ---- ANTLR grammar ----

python:
	pip3 install antlr4-python3-runtime==${antlr_version}

test-antlr:
	java org.antlr.v4.Tool

gen:
	${antlr4} -no-listener -visitor -Dlanguage=Python3 ${language_lib}

# ---- rtl_scan CLI ----

run:
	@python3 -m src $(ARGS)

test:
	python3 test/test_gpio.py
	python3 test/test_multi.py
	python3 test/test_rtl_scan.py

# ---- build binary ----

build:
	pyinstaller rtl_scan.spec --clean

install: build
	@cp -v dist/rtl_scan /usr/local/bin/rtl_scan 2>/dev/null || \
	 cp -v dist/rtl_scan $$HOME/.local/bin/rtl_scan
	@echo "Installed: $$(which rtl_scan 2>/dev/null || echo $$HOME/.local/bin/rtl_scan)"

clean:
	rm -rf build/ dist/ __pycache__ src/__pycache__

# ---- convenience ----

help:
	@python3 -m src --help

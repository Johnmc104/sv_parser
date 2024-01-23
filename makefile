#need java11
language=verilog
antlr_version=4.8
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
python_cmd=run_sv.py test.sv
else ifeq (${language}, verilog)
language_lib=${verilog}
python_cmd=run_v.py test.v
endif

python:pip3 install antlr4-python3-runtime==${antlr_version}

test:
	java org.antlr.v4.Tool

gen:
	${antlr4} -no-listener -visitor -Dlanguage=Python3 ${language_lib}

run:
	@python3 ${python_cmd}

build:
	pyinstaller run_v.py
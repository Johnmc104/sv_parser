import string
import sys
import time
from antlr4 import FileStream, CommonTokenStream

from verilog.VerilogLexer import VerilogLexer
from verilog.VerilogParser import VerilogParser
from verilog.VerilogParserVisitor import VerilogParserVisitor
from verilog.VerilogPreParser import VerilogPreParser
from verilog.VerilogPreParserVisitor import VerilogPreParserVisitor

import re

def print_matches(text):
  matches = re.findall(r'(input|output|inout)(wire|reg)?(?:\[(\d+):(\d+)\])?(\w+)', text)
  for match in matches:
    dir, type, start, end, name = match
    if start != '':
      print(f'{dir} {type} {start}:{end} {name}')
    else :
      print(f'{dir} {type} {name}')

class moduleVisitor(VerilogParserVisitor):
  def visitPort_declaration(self, ctx: VerilogParser.Port_declarationContext):
    rtn = ctx.inout_declaration()
    if rtn is not None: 
      print('inout:',rtn.getText())
 
    rtn = ctx.input_declaration()
    if rtn is not None: 
      print('input:',rtn.getText())
      print_matches(rtn.getText())

    rtn = ctx.output_declaration()
    if rtn is not None: 
      print('output:',rtn.getText())



def main(argv):
  start = time.time()

  input_stream = FileStream('test.v')
  lexer = VerilogLexer(input_stream)
  stream = CommonTokenStream(lexer)
  parser = VerilogParser(stream)

  visitor = moduleVisitor()
  context = parser.source_text()
  ast = visitor.visitSource_text(context)

  print(f"Elapsed time: {time.time() - start} s")

if __name__ == "__main__":
  main(sys.argv)
import string
import sys
import os
import time
from antlr4 import FileStream, CommonTokenStream

from verilog.VerilogLexer import VerilogLexer
from verilog.VerilogParser import VerilogParser
from verilog.VerilogParserVisitor import VerilogParserVisitor
from verilog.VerilogPreParser import VerilogPreParser
from verilog.VerilogPreParserVisitor import VerilogPreParserVisitor

import re

class ParseResult:
  def __init__(self):
    self.ports = [] # list of dict

  def set_ports(self, matches):
    for i, match in enumerate(matches):
      dir, type, start, end, name = match

      result = {}
      if dir    != '': result['dir'] = dir
      if type   != '': result['type'] = type
      if start  != '': 
        result.update({'msb': start, 'lsb': end, 'name': name })
      else : 
        result['name'] = name

      self.ports.append(result)
      #print( "name: ", name, result)



  def get_port_matches(self, text):
    matches = re.findall(r'(input|output|inout)(wire|reg)?(?:\[(\d+):(\d+)\])?(\w+)', text)

    if len(matches) > 0:
      self.set_ports(matches)
    else:
      print("No results to update.")


class moduleVisitor(VerilogParserVisitor):
  def __init__(self):
    self.results = ParseResult()

  def visitPort_declaration(self, ctx: VerilogParser.Port_declarationContext):
    rtn = ctx.inout_declaration()
    if rtn is not None: 
      #print('inout:',rtn.getText())
      self.results.get_port_matches(rtn.getText())
 
    rtn = ctx.input_declaration()
    if rtn is not None: 
      #print('input:',rtn.getText())
      self.results.get_port_matches(rtn.getText())

    rtn = ctx.output_declaration()
    if rtn is not None: 
      #print('output:',rtn.getText())
      self.results.get_port_matches(rtn.getText())


def main(argv):
  start = time.time()

  if len(sys.argv) > 1:
      filename = sys.argv[1]
  else:
      filename = 'test.v'  # default filename

  if not os.path.exists(filename):
      print(f"File {filename} does not exist.")
      sys.exit(1)

  input_stream = FileStream(filename)
  lexer = VerilogLexer(input_stream)
  stream = CommonTokenStream(lexer)
  parser = VerilogParser(stream)

  visitor = moduleVisitor()
  context = parser.source_text()
  ast = visitor.visitSource_text(context)

  #print("=====================================")
  #for port in visitor.results.ports:
  #  print("Signal: ", port)

  print(f"Elapsed time: {time.time() - start} s")

if __name__ == "__main__":
  main(sys.argv)
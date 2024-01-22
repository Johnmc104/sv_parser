import string
import sys
import time
from antlr4 import FileStream, CommonTokenStream
from systemverilog.SystemVerilogLexer import SystemVerilogLexer
from systemverilog.SystemVerilogParser import SystemVerilogParser
from systemverilog.SystemVerilogParserVisitor import SystemVerilogParserVisitor
from systemverilog.SystemVerilogPreParser import SystemVerilogPreParser
from systemverilog.SystemVerilogPreParserVisitor import SystemVerilogPreParserVisitor


class classVisitor(SystemVerilogParserVisitor):
  def visitClass_declaration(self, ctx: SystemVerilogParser.Class_declarationContext):
    rtn = ctx.class_identifier()
    if rtn is not None: 
      print('class:',rtn.getText())

    rtn = ctx.class_extension() 
    if rtn is not None: 
      #print('class_extens:',rtn)
      name = rtn.getText()
      name = name.lstrip("extends")
      print('class_extens:',name)

    rtn = ctx.class_implementation() 
    if rtn is not None: 
      name = rtn.getText()
      name = name.lstrip("implements")
      print('class_implements:',name)

    self.visitChildren(ctx)

  def visitFunction_identifier(self, ctx: SystemVerilogParser.Function_identifierContext):
    rtn = ctx.identifier()
    if rtn is not None:
      print('function:',rtn.getText())


def main(argv):
  start = time.time()

  input_stream = FileStream('test.sv')
  lexer = SystemVerilogLexer(input_stream)
  stream = CommonTokenStream(lexer)
  parser = SystemVerilogParser(stream)
  
  visitor = classVisitor()
  context = parser.source_text()
  ast = visitor.visitSource_text(context)

  print(f"Elapsed time: {time.time() - start} s")

if __name__ == "__main__":
  main(sys.argv)

#class classVisitor(SystemVerilogParserVisitor):
#  def visitClass_declaration(self, ctx: SystemVerilogParser.Class_declarationContext):
#    if len(rtn := ctx.class_identifier()):
#      for tmp in rtn: print('class:',tmp.getText())
#    if rtn := ctx.class_type():print('class_type:',rtn.getText())
#    print("=========")
#    self.visitChildren(ctx)
#
#  def visitFunction_identifier(self, ctx: SystemVerilogParser.Function_identifierContext):
#    if rtn := ctx.identifier():print('function:',rtn.getText())

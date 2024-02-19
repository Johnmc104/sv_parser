from antlr4 import InputStream, FileStream, CommonTokenStream
import antlr4

from verilog.VerilogLexer import VerilogLexer
from verilog.VerilogParser import VerilogParser
from verilog.VerilogParserVisitor import VerilogParserVisitor
from verilog.VerilogPreParser import VerilogPreParser
from verilog.VerilogPreParserVisitor import VerilogPreParserVisitor

from .ParseResult import ParseResult
from .vModuleInstance import Visitor_ModuleInstance, Visitor_InstantiationContext

module_id = 0

#class Vistor_Description(VerilogParserVisitor):
#  def __init__(self, results: ParseResult):
#  self.results = results
#
#  def visitDescription(self, ctx:VerilogParser.Module_declarationContext):
#    print('description:',ctx.getText())

class Visitor_Module(VerilogParserVisitor):
  def __init__(self, results: ParseResult):
    self.results = results

  def visitModule_declaration(self, ctx:VerilogParser.Module_declarationContext):
    global module_id
    #print('module:',ctx.getText())
    #print('type:',type(ctx))

    rtn = ctx.module_identifier()
    if rtn is None: return
    
    module_name = rtn.getText()
    #print('module_name:',module_name)

    self.results.modules[module_id] = {
      'id': module_id,
      'name': module_name,
      'node': ctx,
      'instances': {}
    }



def Design2Tree(design_file):
  lexer = VerilogLexer(InputStream(design_file))
  stream = CommonTokenStream(lexer)
  parser = VerilogParser(stream)
  tree = parser.source_text()
  return tree

def get_module(design:str, results: ParseResult):
  global module_id

  tree = Design2Tree(design)  

  #print(tree.getText())
  #print(type(tree))

  visitor = Visitor_Module(results)
  #visitor.visit(tree)
  ast = visitor.visitSource_text(tree)

  #print("module_id:", module_id)
  #print("ast:\n",ast)

  node = results.modules[module_id]['node']

#  visitor = Visitor_ModuleInstance(module_id,results)
#  #visitor.visit(tree)
#  visitor.visitName_of_module_instance(node)
#  #visitor.visitList_of_port_connections(node)
#
#  visitor = Visitor_InstantiationContext(module_id, results)
#  #visitor.visit(tree)
#  #visitor.visitModule_instantiation(node)
#  visitor.visitModule_identifier(node)

  module_id = module_id + 1


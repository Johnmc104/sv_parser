from antlr4 import InputStream, FileStream, CommonTokenStream
import antlr4

from verilog.VerilogLexer import VerilogLexer
from verilog.VerilogParser import VerilogParser
from verilog.VerilogParserVisitor import VerilogParserVisitor
from verilog.VerilogPreParser import VerilogPreParser
from verilog.VerilogPreParserVisitor import VerilogPreParserVisitor

from .ParseResult import ParseResult

instance_id = 0
instance_id_en = 0

class Visitor_ModuleInstance(VerilogParserVisitor):
  def __init__(self, module_id, results: ParseResult):
    self.module_id = module_id
    self.results = results
    self.instance_name = ''
    #self.instance_id = 0
    

  def visitModule_instance(self, ctx:VerilogParser.Module_instanceContext):
    global instance_id,instance_id_en
    #print(ctx.getText())

    instance_id_en = 1

    rtn = ctx.name_of_module_instance()
    if rtn is not None: 
      #print('instance_name:',rtn.getText())
      self.instance_name = rtn.getText()

      #print ("results:", self.results.modules[self.module_id]["instances"])
      self.results.modules[self.module_id]['instances'][instance_id] = {
        'instance_name' : self.instance_name
      }

    rtn = ctx.list_of_port_connections()
    if rtn is not None: 
      #print('port_list:',rtn.getText())
      port_list = rtn.getText()
      self.results.modules[self.module_id]['instances'][instance_id]['port_list'] = port_list

    instance_id = instance_id + 1
   
class Visitor_InstantiationContext(VerilogParserVisitor):
  def __init__(self, module_id, results: ParseResult):
    self.module_id = module_id
    self.results = results

  def visitModule_instantiation(self, ctx: VerilogParser.Module_instantiationContext):
    global instance_id, instance_id_en
    #print(ctx.getText())

    if instance_id_en == 1:
      instance_id = 0
      instance_id_en = 0

    instance = self.results.modules[self.module_id]['instances'][instance_id]

    rtn = ctx.module_instance()
    if rtn is not None:
      #rtn_len = len(rtn)
      #print("rtn_len:",rtn_len)
      #print('module_instance:',rtn[0].getText())
      instance['node'] = ctx
      
    rtn = ctx.module_identifier()
    if rtn is not None: 
      #print('module_name:',rtn.getText())
      module_name = rtn.getText()
      instance['module_name'] = module_name

    rtn = ctx.parameter_value_assignment()
    if rtn is not None:
      instance['parameter'] = rtn.getText()
    else:
      instance['parameter'] = ''

    instance_id = instance_id + 1

#    rtn = ctx.list_of_port_connections()
#    if rtn is not None:
#      print('port_list:',rtn.getText())
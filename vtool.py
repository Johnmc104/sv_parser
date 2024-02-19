import string
import sys
import os
import time
import re
import argparse

from verilog.VerilogLexer import VerilogLexer
from verilog.VerilogParser import VerilogParser
from verilog.VerilogParserVisitor import VerilogParserVisitor
from verilog.VerilogPreParser import VerilogPreParser
from verilog.VerilogPreParserVisitor import VerilogPreParserVisitor

from antlr4 import InputStream, FileStream, CommonTokenStream
import antlr4

import src
from src.ParseResult import ParseResult
from src.vModule import Visitor_Module, Design2Tree, get_module
from src.vModuleInstance import Visitor_ModuleInstance, Visitor_InstantiationContext

class ModuleInstantiationVisitor(VerilogParserVisitor):
  def __init__(self, results):
    self.is_first_instantiation_module = False
    self.module_identifier = ""
    self.name_of_module_instance = ""
    self.list_of_ports_rhs = []
    self.list_of_ports_rhs_width = []

  def visitModule_instantiation(self, ctx: VerilogParser.Module_instantiationContext):
    if self.is_first_instantiation_module == False:
      self.is_first_instantiation_module = True
      self.first_instantiation = ctx

      rtn = ctx.module_identifier()
      if rtn is not None: 
        #print ("module_identifier:", rtn.getText())
        self.module_identifier = rtn.getText()

#      rtn = ctx.parameter_value_assignment()
#      if rtn is not None: 
#        print ("parameter_value_assignment:", rtn.getText())
#        self.vparameter_value_assignment = rtn.getText()

      module_instance = ctx.module_instance()

      #print ("module_instances:", len(module_instance))

      if module_instance is not None and len(module_instance) > 0:
        rtn = module_instance[0]
        self.name_of_module_instance = rtn.name_of_module_instance().getText()

        
        # get ports connections
        ports_connections = module_instance[0].list_of_port_connections()

        #print("ports_connections:", ports_connections.getText())
        for child in ports_connections.getChildren():
          self.list_of_ports_rhs.append(child.expression().getText())



def get_tree(design:str, results: ParseResult):
  tree = Design2Tree(design)  

  visitor = Visitor_Module(results)
  visitor.visit(tree)



#def view_tree(tree):
#  G = nx.DiGraph()
#
#  # 添加节点，每个节点是一个字典
#  G.add_node('module1', attr_dict={'name': 'module1', 'ports': ['port1', 'port2']})
#  G.add_node('module2', attr_dict={'name': 'module2', 'ports': ['port3', 'port4']})
#
#  # 添加边
#  G.add_edge('module1', 'module2')


def read_multiple_files(file_list):
  return [file_name.strip() for file_name in file_list]

def main(argv):
  start = time.time()

  # 创建一个ArgumentParser对象
  parser = argparse.ArgumentParser(description='这是一个参数选项的示例程序')

  # 添加参数选项
  parser.add_argument('-f', '--file', help='指定文件名')
  parser.add_argument('-top', '--top', help='指定设计顶层')

  # 解析命令行参数
  args = parser.parse_args()

  #--------------------------------------------------------------
  parse_result = ParseResult()
  parse_result.top_name = args.top
    
  file_names = args.file
    
  with open('filelist', 'r') as f:
    filelists = f.readlines()

  filelists = [filename.strip() for filename in filelists]

  #print (filelists)

#  file_path = '/home/zhhe/work/soc_m0/rtl/logical/cmsdk_ahb_gpio/verilog/cmsdk_ahb_gpio.v'
#  with open(file_path,"r") as file:
#    design = file.read()

  for file in filelists:
    #print ("file:", file)
    with open(file,"r") as file:
      design = file.read()

    get_module(design, parse_result)

  parse_result.print_modules()
  parse_result.find_top_id()

  #print (parse_result.modules[parse_result.top_name]['instances'])
  #print (parse_result.modules)
  #print ("top_name:",parse_result.top_name)

  #print("=====================================")
  #for port in parse_result.ports:
  #  print("Signal: ", port)

  print(f"Elapsed time: {time.time() - start} s")

if __name__ == "__main__":
  main(sys.argv)
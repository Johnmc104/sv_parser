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
    self.modules = []
    self.ports = [] # list of dict
    self.params = []

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
    #print(self.params)

    #replace param
    for i, param in enumerate(self.params):
      param_name = param['name']
      param_value = param['value']
      param_value = int(param_value) - 1
      param_value = str(param_value)
      pattern = f'{param_name}-1'
      #print (pattern)
      #text = text.replace(pattern, param_value)
      text = re.sub(pattern, param_value, text)

    #print(text)

    matches = re.findall(r'(input|output|inout)(wire|reg|signed)?(?:\[(\d+):(\d+)\])?(\w+)', text)

    if len(matches) > 0:
      self.set_ports(matches)
    else:
      print("No results to update.")

  def get_param_matches(self, text):
    matches = re.findall(r'(\w+)\s*=\s*(\d+)', text)

    #print (matches)

    for i, match in enumerate(matches):
      result = {}
      name, value = match

      name = name.replace('parameter', '')
      result['name'] = name
      result['value'] = value

      self.params.append(result)

    #print (self.params)


  def gen_inst(self):
    module_name = self.modules[0]

    msg_inst = f"{module_name} inst_{module_name}(\n"
    #print(f"module inst_{module_name}(")

    t_ports = []
    for i, port in enumerate(self.ports):
      t_ports.append(port['name'])

    #print(temp_ports)
      
    t_ports = [port.replace('i_', 'w_').replace('o_', 'w_') for port in t_ports]

    max_len = max(len(port) for port in t_ports)

    msg_port_dec = ""
    for i, port in enumerate(t_ports):
      org_port = self.ports[i]

      # gen port info
      msg_port_info = ""
      if org_port['dir']   != '': 
        if org_port['dir'] == 'input':
          msg_port_info += f"{org_port['dir']}  "
        else:
          msg_port_info += f"{org_port['dir']} "
      if 'type' in org_port and org_port['type']  != '': 
        if org_port['type'] == 'reg':
          msg_port_info += f"{org_port['type']}  "
        else:
          msg_port_info += f"{org_port['type']} "
      if 'msb' in org_port and org_port['msb']   != '':
        msg_port_info += f"[{org_port['msb']}:{org_port['lsb']}] "

        # check if signal starts with 'w_' and generate signal declaration
        if port.startswith('w_'):
          size = int(org_port['msb']) - int(org_port['lsb']) + 1
          msg_port_dec += f"wire [{size-1}:0] {port}; \n"
      #if org_port['name']  != '': 
      #  msg_port_info += f"{org_port['name']} "
      #print(msg_port_info)

      if i == len(t_ports) - 1:
        #print(f"  .{org_port['name']:<{max_len}} ({port:<{max_len}} ) // {msg_port_info}")
        msg_inst += f"  .{org_port['name']:<{max_len}} ({port:<{max_len}} ) // {msg_port_info}\n"
      else:
        #print(f"  .{org_port['name']:<{max_len}} ({port:<{max_len}} ),// {msg_port_info}")
        msg_inst += f"  .{org_port['name']:<{max_len}} ({port:<{max_len}} ),// {msg_port_info}\n"

    msg_inst += f");"

    print(msg_port_dec)
    print(msg_inst)


class PortVisitor(VerilogParserVisitor):
  def __init__(self, results):
    self.results = results

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

class ModuleVisitor(VerilogParserVisitor):
  def __init__(self, results):
    self.results = results

  def visitModule_declaration(self, ctx:VerilogParser.Module_declarationContext):
    rtn = ctx.module_identifier()
    if rtn is not None: 
      #print('module_name:',rtn.getText())
      self.results.modules.append(rtn.getText())

    rtn = ctx.module_parameter_port_list()
    if rtn is not None: 
      #print('param_list:',rtn.getText())
      self.results.get_param_matches(rtn.getText())
      
    #rtn = ctx.list_of_port_declarations()
    #if rtn is not None: 
    #  print('port_list:',rtn.getText())
    #  #self.results.ports.append(rtn.getText())
    #  #self.results.get_port_matches(rtn.getText())


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
  context = parser.source_text()

  parse_result = ParseResult()

  visitor_module = ModuleVisitor(parse_result)
  ast = visitor_module.visitSource_text(context)

  visitor_port = PortVisitor(parse_result)
  ast = visitor_port.visitSource_text(context)
  
  #print (ast)

  #print("=====================================")
  #for port in parse_result.ports:
  #  print("Signal: ", port)

  parse_result.gen_inst()

  print(f"Elapsed time: {time.time() - start} s")

if __name__ == "__main__":
  main(sys.argv)
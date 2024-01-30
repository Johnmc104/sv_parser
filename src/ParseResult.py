from pprint import pprint

class ParseResult:
  def __init__(self):
    self.top_name = "tb_top"
    self.modules = {}

  def print_modules(self):
    #print (self.modules[self.top_name]['instances'])
    pprint(self.modules)
    #for module in self.modules:
    #  print(module['name'])


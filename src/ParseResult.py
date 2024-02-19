from pprint import pprint

class ParseResult:
  def __init__(self):
    self.top_name = "tb_top"
    self.top_id = 0
    self.modules = {}

  def print_modules(self):
    #print (self.modules[self.top_name]['instances'])
    pprint(self.modules)
    #for module in self.modules:
    #  print(module['name'])

  def find_top_id(self):
    for module in self.modules:
      if self.modules[module]['name'] == self.top_name:
        self.top_id = self.modules[module]['id']
        break

    print ("top_id:",self.top_id)
     

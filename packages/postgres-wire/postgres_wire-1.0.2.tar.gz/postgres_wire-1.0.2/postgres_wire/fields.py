class BoolField:
  def __init(self, name):
    self.name = name
    self.type_id = 16
    self.type_size = 1

class IntField:
  def __init__(self, name):
    self.name = name
    self.type_id = 23
    self.type_size = 4

# Based on https://github.com/jeroenrinzema/psql-wire/blob/029cb6a10c1b8d5a9076e12f714c57d672f3e898/examples/copy/main.go#L22
class TextField:
  def __init__(self, name):
    self.name = name
    self.type_id = 25
    self.type_size = 256

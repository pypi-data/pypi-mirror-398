import struct

class PgBuffer(object):
  def __init__(self, stream):
    self.buffer = stream

  def read_byte(self):
    return self.read_bytes(1)

  def read_bytes(self, n):
    data = self.buffer.read(n)
    if not data:
      raise Exception("No data")
    return data

  def read_int32(self):
    data = self.read_bytes(4)
    return struct.unpack("!i", data)[0]

  def read_parameters(self, n):
    data = self.read_bytes(n)
    return data.split(b'\x00')

  def write_byte(self, value):
    self.buffer.write(value)

  def write_bytes(self, value):
    self.buffer.write(value)

  def write_int16(self, value):
    self.buffer.write(struct.pack("!h", value))

  def write_int32(self, value):
    self.buffer.write(struct.pack("!i", value))

  def write_string(self, value):
    self.buffer.write(value.encode() if isinstance(value, str) else value)
    self.buffer.write(b'\x00')

  def write_parameters(self, kvs):
    data = ''.join(['%s\x00%s\x00' % kv in kvs])
    self.buffer.write_int32(4 + len(data))
    self.buffer.write(data)

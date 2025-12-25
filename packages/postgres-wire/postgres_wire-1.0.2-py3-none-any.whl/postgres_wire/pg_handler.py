from io import BytesIO
import socketserver
import struct

from .constants import PSQL_FE_MESSAGES
from .fields import BoolField, IntField, TextField
from .pg_buffer import PgBuffer

class Handler(socketserver.StreamRequestHandler):
  debug = False
  port = 5432

  def handle(self):
    self._pgbuf = PgBuffer(self.rfile)
    self.wbuf = PgBuffer(self.wfile)

    try:
      # Handshake
      self.read_ssl_request()
      self.send_notice()
      self.read_startup_message()

      # Auth
      self.send_authentication_request()
      self.read_authentication()
      self.send_authentication_ok()

      while True:
        self.send_ready_for_query()

        # Read Message
        type_code = self._pgbuf.read_byte()
        if self.debug:
          print(PSQL_FE_MESSAGES.get(type_code))

        if type_code == b'Q':
          msglen = self._pgbuf.read_int32()
          sql = self._pgbuf.read_bytes(msglen - 4)
          self.handle_query(sql)
        elif type_code == b'X':
          break
    except Exception as e:
      if self.debug:
        raise e

  def read_ssl_request(self):
    msglen = self._pgbuf.read_int32()
    sslcode = self._pgbuf.read_int32()
    if msglen != 8 and sslcode != 80877103:
      raise Exception("Unsupported SSL request")

  def read_startup_message(self):
    msglen = self._pgbuf.read_int32()
    version = self._pgbuf.read_int32()
    v_maj = version >> 16
    v_min = version & 0xffff
    msg = self._pgbuf.read_parameters(msglen - 8)

    decoded = [s.decode('utf-8').replace('\x00', '').strip() for s in msg]
    self.parameters = dict(zip(decoded[::2], decoded[1::2]))

  def read_authentication(self):
    type_code = self._pgbuf.read_byte()
    if type_code != b"p":
      self.send_error("FATAL", "28000", "authentication failure")
      raise Exception("Only 'Password' auth is supported, got %r" % type_code)

    msglen = self._pgbuf.read_int32()
    password = self._pgbuf.read_bytes(msglen - 4)

    if hasattr(self, "check_auth"):
      self.check_auth(self.parameters['user'], password.decode("utf-8").replace('\x00', '').strip())

  def send_notice(self):
    self.wfile.write(b'N')

  def send_authentication_request(self):
    self.wfile.write(struct.pack("!cii", b'R', 8, 3))

  def send_authentication_ok(self):
    self.wfile.write(struct.pack("!cii", b'R', 8, 0))

  def send_ready_for_query(self):
    self.wfile.write(struct.pack("!cic", b'Z', 5, b'I'))

  def send_command_complete(self, tag):
    self.wfile.write(struct.pack("!ci", b'C', 4 + len(tag)))
    self.wfile.write(tag)

  def send_error(self, severity, code, message):
    buf = PgBuffer(BytesIO())
    buf.write_byte(b'S')
    buf.write_string(severity)
    buf.write_byte(b'C')
    buf.write_string(code)
    buf.write_byte(b'M')
    buf.write_string(message)
    buf = buf.buffer.getvalue()

    self.wbuf.write_byte(b'E')
    self.wbuf.write_int32(4 + len(buf))
    self.wbuf.write_string(buf)

  def send_row_description(self, fields):
    buf = PgBuffer(BytesIO())
    for field in fields:
      buf.write_string(field.name)
      buf.write_int32(0)    # Table ID
      buf.write_int16(0)    # Column ID
      buf.write_int32(field.type_id)
      buf.write_int16(field.type_size)
      buf.write_int32(-1)   # type modifier
      buf.write_int16(0)    # text format code
    buf = buf.buffer.getvalue()

    self.wbuf.write_byte(b'T')
    self.wbuf.write_int32(6 + len(buf))
    self.wbuf.write_int16(len(fields))
    self.wbuf.write_bytes(buf)

  def send_row_data(self, rows):
    for row in rows:
      buf = PgBuffer(BytesIO())
      for field in row:
        v = b'%r' % field
        buf.write_int32(len(v))
        buf.write_bytes(v)
      buf = buf.buffer.getvalue()

      self.wbuf.write_byte(b'D')
      self.wbuf.write_int32(6 + len(buf))
      self.wbuf.write_int16(len(row))
      self.wbuf.write_bytes(buf)

  def handle_query(self, sql):
    rows = self.query(sql)
    if len(rows) == 0:
      self.send_row_description([])
      self.send_row_data([])

      self.send_command_complete(b'SELECT\x00')

    # Making sure all rows are of the same type
    for i in range(len(rows)-1):
      assert type(rows[i]) == type(rows[i+1])

    fields = []
    for field_name, field_info in type(rows[0]).model_fields.items():
      if field_info.annotation is int:
        fields += [IntField(field_name)]
      elif field_info.annotation is str:
        fields += [TextField(field_name)]
      elif field_info.annotation is bool:
        fields += [BoolField(field_name)]
      else:
        raise ValueError(f"Got unsupported type {field_info.annotation}")

    rows = [list(getattr(row, f.name) for f in fields) for row in rows]

    self.send_row_description(fields)
    self.send_row_data(rows)

    self.send_command_complete(b'SELECT\x00')

  def query(self, sql):
    raise NotImplemented



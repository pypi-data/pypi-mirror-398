import socketserver

class Server(socketserver.TCPServer):
  allow_reuse_address = True

def create_server(handler):
  server = Server(("localhost", 5432), handler)
  return server

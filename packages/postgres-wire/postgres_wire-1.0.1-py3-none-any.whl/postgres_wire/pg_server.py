import socketserver

class Server(socketserver.TCPServer):
  allow_reuse_address = True

def create_server(handler):
  server = Server(("0.0.0.0", handler.port), handler)
  def run():
    try:
      print(f"Listening at 0.0.0.0:{handler.port}")
      server.serve_forever()
    except:
      server.shutdown()
  return run

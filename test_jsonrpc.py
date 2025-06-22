from jsonrpcserver import method, dispatch, Success
from http.server import BaseHTTPRequestHandler, HTTPServer

@method
def test_method():
    return Success("Hello, MCP, PLEASE REPLY!")

class JsonRpcHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        request_data = self.rfile.read(content_length).decode('utf-8')
        response = dispatch(request_data)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(str(response).encode('utf-8'))

if __name__ == "__main__":
    server_address = ('localhost', 5000)
    httpd = HTTPServer(server_address, JsonRpcHandler)
    print("JSON-RPC server running on localhost:5000")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down server")
        httpd.server_close()

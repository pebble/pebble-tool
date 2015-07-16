import BaseHTTPServer
import socket
import urlparse
import urllib
import webbrowser


class BrowserController(object):
    def __init__(self):
        self.port = None

    def open_config_page(self, url, callback):
        self.port = port = self._find_port()
        url = self.url_append_params(url, {'return_to': 'http://localhost:{}/close?'.format(port)})
        webbrowser.open_new(url)
        self.serve_page(port, callback)

    def serve_page(self, port, callback):
        # This is an array so AppConfigHandler doesn't create an instance variable when trying to set the state to False
        running = [True]

        class AppConfigHandler(BaseHTTPServer.BaseHTTPRequestHandler):
            def do_GET(self):
                path, query = self.path.split('?', 1)
                if path == '/close':
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write("OK")
                    running[0] = False
                    callback(query)
                else:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write("Not Found")

        server = BaseHTTPServer.HTTPServer(('', port), AppConfigHandler)
        while running[0]:
            server.handle_request()

    def url_append_params(self, url, params):
        parsed = urlparse.urlparse(url, "http")
        query = parsed.query
        if parsed.query != '':
            query += '&'

        encoded_params = urllib.urlencode(params)
        query += encoded_params
        return urlparse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, query, parsed.fragment))

    def _find_port(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('localhost', 0))
        addr, port = s.getsockname()
        s.close()
        return port

from fetch_teams.bottle import bottle

class SSLWSGIRefServer(bottle.ServerAdapter):
    def __init__(self, certificate_file=None, **kwargs):
        self.certificate_file = certificate_file
        super(SSLWSGIRefServer, self).__init__(**kwargs)
        self.srv = None

    def run(self, handler):
        from wsgiref.simple_server import make_server, WSGIRequestHandler
        import ssl
        try:
            if self.quiet:
                class QuietHandler(WSGIRequestHandler):
                    def log_request(*args, **kw):
                        print(args, kw)
                self.options['handler_class'] = QuietHandler
            srv = make_server(self.host, self.port, handler, **self.options)
            srv.socket = ssl.wrap_socket (
                srv.socket,
                certfile=self.certificate_file,  # path to certificate
                server_side=True)

            self.srv = srv
            srv.serve_forever()
        except Exception as e:
            print("************* SSLWSGIRefServer exception: ", e)

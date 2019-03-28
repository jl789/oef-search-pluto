from api.src.python.BackendRouter import BackendRouter
import asyncio
from fetch_teams.bottle import SSLWSGIRefServer
from fetch_teams.bottle import bottle
from network.src.python.async_socket.AsyncSocket import run_server, handler, Transport
from utils.src.python.Logging import get_logger
from functools import partial
import utils.src.python.resources as resources
import os
from concurrent.futures import ThreadPoolExecutor


def socket_handler(router: BackendRouter):
    log = get_logger("SocketConnectionHandler")

    @handler
    async def on_connection(transport: Transport):
        log.info("Got socket client")
        path, data = await transport.read()
        response = await router.route(path, data)
        await transport.write(response)
        transport.close()
    return on_connection


def http_json_handler(router):
    log = get_logger("HttpJsonRequestHandler")

    def on_request(path=""):
        log.info("Got json request over http")
        try:
            response = asyncio.run(router.route(path, bottle.request.json))
            bottle.response.headers['Content-Type'] = 'application/json'
            return response
        except bottle.HTTPError as e:
            log.error("Not valid JSON request: ", e)
    return on_request


def socket_server(host: str, port: str, router: BackendRouter):
    asyncio.run(run_server(socket_handler(router), host, port))


def serve_site(html_dir: str, path: str):
    if path.find(".js") > 0:
        bottle.response.headers['Content-Type'] = 'text/javascript'
    elif path.find(".css") > 0:
        bottle.response.headers['Content-Type'] = 'text/css'
    return resources.textfile(os.path.join(html_dir, path))


def http_server(host: str, port: int, crt_file: str, *, router: BackendRouter, html_dir: str = None):
    resources.initialise(__package__)
    app = bottle.Bottle()
    srv = SSLWSGIRefServer.SSLWSGIRefServer(host=host, port=port, certificate_file=crt_file)
    app.route(path="/json/<path:path>", method="POST", callback=http_json_handler(router))
    if html_dir is not None:
        app.route(path="/website/<path:path>", method="GET", callback=partial(serve_site, html_dir))
        app.route(path="/", method="GET", callback=partial(serve_site, html_dir, "index.html"))
    bottle.run(server=srv, app=app)


class CommunicationHandler:
    def __init__(self, max_threads):
        self.handlers = []
        self.executor = ThreadPoolExecutor(max_workers=max_threads)
        self._router = None

    def add(self, *args, **kwargs):
        self.handlers.append((args[0], args[1:], kwargs))

    def set_router(self, router: BackendRouter):
        self._router = router

    def start(self, router: BackendRouter):
        for handler in self.handlers:
            print("Start handler: ", handler)
            self.executor.submit(handler[0], *handler[1], **handler[2], router=router)

    def wait(self):
        self.executor.shutdown(wait=True)

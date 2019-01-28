from concurrent.futures import ThreadPoolExecutor
import asyncio
from network.src.python.async_socket.AsyncSocket import run_server, handler, Transport
from api.src.python.BackendRouter import BackendRouter
from third_party.bottle import SSLWSGIRefServer
from third_party.bottle import bottle
import sys
from api.src.python.EndpointSearchQuery import SearchQuery


def socket_handler(router: BackendRouter):
    @handler
    async def on_connection(transport: Transport):
        print("Got socket client")
        path, data = await transport.read()
        response = await router.route(path, data)
        await transport.write(response)
        transport.close()
    return on_connection


def run_socket_server(host: str, port: str, router: BackendRouter):
    asyncio.run(run_server(socket_handler(router), host, port))


def http_json_handler(router):
    def on_request(path=""):
        try:
            response = asyncio.run(router.route(path, bottle.request.json))
            bottle.response.headers['Content-Type'] = 'application/json'
            return response
        except bottle.HTTPError as e:
            print("Not valid JSON request: ", e)
    return on_request


def run_http_server(host: str, port: int, crt_file: str, router: BackendRouter):
    app = bottle.Bottle()
    srv = SSLWSGIRefServer.SSLWSGIRefServer(host=host, port=port, certificate_file=crt_file)
    app.route(path="/json/<path:path>", method="POST", callback=http_json_handler(router))
    bottle.run(server=srv, app=app)


if __name__ == "__main__":
    executor = ThreadPoolExecutor(max_workers=2)
    http_port_number = int(sys.argv[1])
    certificate_file = sys.argv[2]
    socket_port_number = http_port_number+1
    if len(sys.argv) == 4:
        socket_port_number = sys.argv[3]

    #modules
    search_module = SearchQuery()
    #router
    router_ = BackendRouter()
    router_.register_serializer("search", search_module)
    router_.register_handler("search", search_module)

    executor.submit(run_socket_server, "0.0.0.0", socket_port_number, router_)
    executor.submit(run_http_server, "0.0.0.0", http_port_number, certificate_file, router_)
    executor.shutdown(wait=True)

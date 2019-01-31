from api.src.python.Interfaces import HasMessageHandler, HasProtoSerializer
from api.src.python.Serialization import serializer, deserializer
from utils.src.python.Logging import has_logger
from fetch_teams.oef_core_protocol import query_pb2
from api.src.proto import response_pb2
from ai_search_engine.src.python.SearchEngine import SearchEngine


class UpdateEndpoint(HasProtoSerializer, HasMessageHandler):
    @has_logger
    def __init__(self, search_engine: SearchEngine):
        self.search_engine = search_engine

    @serializer
    def serialize(self, data: bytes) -> query_pb2.Query.DataModel:
        pass

    @deserializer
    def deserialize(self, proto_msg: response_pb2.UpdateResponse) -> bytes:
        pass

    async def handle_message(self, msg: query_pb2.Query.DataModel) -> response_pb2.Response:
        self.log.info("Got message: ")
        print(msg)
        self.search_engine.add(msg)
        resp = response_pb2.Response()
        return resp

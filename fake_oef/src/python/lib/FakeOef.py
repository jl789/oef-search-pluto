import asyncio
from api.src.proto.core import update_pb2
import abc
from fake_oef.src.python.lib.ConnectionFactory import SupportsConnectionInterface
from fake_oef.src.python.lib import FakeBase
from fake_oef.src.python.lib.Connection import Connection
from api.src.proto.core import update_pb2, response_pb2
from fetch_teams.oef_core_protocol import query_pb2
import re
from utils.src.python.Logging import has_logger


class SearchComInterface(abc.ABC):
    def call(self, path: str, data):
        pass


def create_address_attribute_update(key: str, ip: str, port: int):
    attr = update_pb2.Update.Attribute()
    key = key.encode("utf-8")
    attr.name = update_pb2.Update.Attribute.Name.Value("NETWORK_ADDRESS")
    attr.value.type = 10
    attr.value.a.ip = ip
    attr.value.a.port = port
    attr.value.a.key = key
    attr.value.a.signature = "Signed".encode("utf-8")
    upd = update_pb2.Update()
    upd.key = key
    upd.attributes.extend([attr])
    return upd


class FakeOef(FakeBase.FakeBase, SupportsConnectionInterface):
    @has_logger
    def __init__(self, **kwargs):
        for k in ['id', 'port', 'connection_factory']:
            setattr(self, k, kwargs.get(k, None))
        if not self.port:
            self.port = int(re.sub(r"[^0-9]", "", self.id))
        self.connections = {}
        self.service_directory = {}
        if self.connection_factory:
            self.connection_factory.add_obj(self.id, self)
        self.search_com = None
        self._bin_id = self.id.encode("utf-8")
        super().__init__(self.id, **kwargs)

    @property
    def connection(self):
        return self.connections

    @connection.setter
    def connection(self, value):
        self.connections = value

    def connect_to_search(self, search_id):
        self.log.info("Create connection to search node %s, and registering localhost:%d", search_id, self.port)
        self.search_com = self.connection_factory.create(search_id, self.id)
        self.search_com.call("update", create_address_attribute_update(self.id, "127.0.0.1", self.port))

    def disconnect_search(self):
        self.search_com.disconnect()

    async def async_search(self, query):
        self.log.info("Got search query with TTL %d", query.ttl)
        my_location = self.search_com.call("get", "location")
        my_distance = my_location.distance(query.directed_search.target.geo)
        query.source_key = self._bin_id
        query.directed_search.distance.geo = my_distance+1.
        result = await self.search_com.call_node("search", query)
        res = response_pb2.SearchResponse()
        res.ParseFromString(result)
        for r in res.result:
            if r.key == self._bin_id:
                res.result.remove(r)
        return res

    def search(self, query):
        return asyncio.run(self.async_search(query))

    def get(self, what):
        if what == "location":
            return self.search_com.call("get", "location")

    async def async_register_service(self, agent_id, service_update):
        self.error("OEF got service from agent {}".format(agent_id))
        upd = service_update
        if not isinstance(service_update, update_pb2.Update):
            upd = update_pb2.Update()
            upd.key = self._bin_id
            dm_instance = update_pb2.Update.DataModelInstance()
            dm_instance.key = agent_id.encode("UTF-8")
            if isinstance(service_update, query_pb2.Query.Instance):
                dm = service_update.model
                dm_instance.values.extend(service_update.values)
                #TODO service_update.values
            else:
                dm = query_pb2.Query.DataModel()
                dm.ParseFromString(service_update)
            dm_instance.model.CopyFrom(dm)
            upd.data_models.extend([dm_instance])
        self.service_directory[agent_id] = service_update
        await self.search_com.call_node("update", upd)

    def register_service(self, agent_id, service_update):
        return asyncio.run(self.async_register_service(agent_id, service_update))

    def unregister_service(self, agent_id):
        self.search_com.call("remove", self.service_directory[agent_id])
        self.service_directory.pop(agent_id, None)

from fake_oef.src.python.lib import Connection
from utils.src.python.Logging import has_logger
import abc
from fake_oef.src.python.lib import Connection


class Endpoint:
    def __init__(self, target, target_id, source_id):
        if not isinstance(target, SupportsConnectionInterface):
            raise TypeError("Creating endpoint for object which doesn't implement the SuppportConnectionInterface not permitted!")
        self._target = target
        self._source_id = source_id
        self._target_id = target_id
        self.id = target_id

    def __getattr__(self, item):
        return getattr(self._target, item)


class ConnectionFactory(object):
    @has_logger
    def __init__(self):
        self._obj_store = {}
        self._addr_store = {}
        self.config = dict()

    def set_search_address(self, host, port):
        self.config["host"] = host
        self.config["port"] = port

    def set_search_node(self, obj_id, obj):
        if not hasattr(obj, "start_network"):
            self.error("Search node object must be decorated with network_support annotation!")
            return
        if obj_id in self._obj_store and obj != self._obj_store[obj_id]:
            raise KeyError("Different object in the store with the same id: {}".format(obj_id))
        self._obj_store[obj_id] = obj


    def add_addr(self, obj_id, addr):
        if obj_id in self._addr_store and addr != self._addr_store[obj_id]:
            raise KeyError("Different address in the store with the same id: {}".format(obj_id))
        self._addr_store[obj_id] = addr

    def clear(self, what = None):
        keys = self._obj_store.keys()
        if what is not None:
            keys = [k for k in keys if k.find(what) != -1]
        for key in keys:
            self._obj_store.pop(key)

    def remove(self, obj_id):
        self._obj_store.pop(obj_id, None)

    def create(self, target, source):
        if target in self._obj_store:
            target_endpoint = Endpoint(self._obj_store[target], target, source)
        else:
            self.log.error("NO TARGET: {}".format(target))
            return None
        if source in self._obj_store:
            source_endpoint = Endpoint(self._obj_store[source], source, target)
        else:
            self.log.error("NO SOURCE: {}".format(source))
            return None
        return Connection.Connection(source_endpoint, target_endpoint)

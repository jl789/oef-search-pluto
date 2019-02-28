import sys

from dap_api.src.python import DapManager
from ai_search_engine.src.python import SearchEngine
from dap_api.experimental.python import InMemoryDap
from dap_api.experimental.python import AddressRegistry
import api.src.python.ProtoWrappers as ProtoWrappers
from api.src.python.EndpointSearch import SearchQuery
from api.src.python.EndpointUpdate import UpdateEndpoint, BlkUpdateEndpoint
from api.src.python.EndpointRemove import RemoveEndpoint
from api.src.python.BackendRouter import BackendRouter
from dap_2d_geo.src.python import DapGeo
from dap_e_r_network.src.python import DapERNetwork


class PlutoApp:
    def __init__(self):
        self.dapManager = DapManager.DapManager()

    def addClass(self, name, maker):
        self.dapManager.addClass(name, maker)

    def setup(self, dapManagerConfig=None):
        if not dapManagerConfig:
            dapManagerConfig = {
                #"key_value_search": {
                #    "class": "InMemoryDap",
                #    "config": {
                #        "structure": {
                #            "value_table": {
                #                "*": "*"
                #            },
                #        },
                #    },
                #},
                "network_search": {
                    "class": "DapERNetwork",
                    "config": {
                        "structure": {
                            "locations": {
                                # actual fields generated by the store.
                            },
                        },
                    },
                },
                "geo_search": {
                    "class": "DapGeo",
                    "config": {
                        "structure": {
                            "locations": {
                                # actual fields generated by the store.
                            },
                        },
                    },
                },
                "data_model_searcher": {
                    "class": "SearchEngine",
                    "config": {
                        "structure": {
                            "data_model_table": {
                                "data_model": "embedding"
                            },
                        },
                    },
                },
                "address_registry": {
                    "class": "AddressRegistry",
                    "config": {
                        "structure": {
                            "address_registry_table": {
                                "address_field": "address"
                            },
                        },
                    },
                }
            }

        self.dapManager.setup(
            sys.modules[__name__],
            dapManagerConfig
        )

        self.dapManager.setDataModelEmbedder('data_model_searcher', 'data_model_table', 'data_model')

        self._setup_endpoints()
        self._setup_router()

    def _setup_endpoints(self):
        AttrName = ProtoWrappers.AttributeName
        update_config = ProtoWrappers.ConfigBuilder(ProtoWrappers.UpdateData)\
            .data_model("data_model_table", "data_model")\
            .attribute(AttrName.Value("LOCATION"), "location_table", "coords")\
            .attribute(AttrName.Value("COUNTRY"), "location_table", "country")\
            .attribute(AttrName.Value("CITY"), "location_table", "city")\
            .attribute(AttrName.Value("NETWORK_ADDRESS"), "address_registry_table", "address_field")\
            .default("default_table", "default_field")\
            .build()

        address_registry = self.dapManager.getInstance("address_registry")

        update_wrapper = ProtoWrappers.ProtoWrapper(ProtoWrappers.UpdateData, update_config, address_registry)
        query_wrapper = ProtoWrappers.ProtoWrapper(ProtoWrappers.QueryData, self.dapManager)


        # endpoints
        self._search_endpoint = SearchQuery(self.dapManager, query_wrapper, address_registry)
        self._update_endpoint = UpdateEndpoint(self.dapManager, update_wrapper)
        self._blk_update_endpoint = BlkUpdateEndpoint(self.dapManager, update_wrapper)
        self._remove_endpoint = RemoveEndpoint(self.dapManager, update_wrapper)

    def _setup_router(self):
        # router
        self.router = BackendRouter()
        self.router.register_response_merger(self._search_endpoint)
        self.router.register_serializer("search", self._search_endpoint)
        self.router.register_handler("search",  self._search_endpoint)
        self.router.register_serializer("update",  self._update_endpoint)
        self.router.register_handler("update",  self._update_endpoint)
        self.router.register_serializer("blk_update",  self._blk_update_endpoint)
        self.router.register_handler("blk_update",  self._blk_update_endpoint)
        self.router.register_serializer("remove", self._remove_endpoint)
        self.router.register_handler("remove", self._remove_endpoint)

    def add_handler(self, path, handler):
        self.router.register_handler(path, handler)

    def start(self, com=None):
        self.setup()
        if com is not None:
            com.start(self.router)

    def getField(self, fieldname):
        return self.dapManager.getField(fieldname)

    async def callMe(self, path, data):
        return await self.router.route(path, data)


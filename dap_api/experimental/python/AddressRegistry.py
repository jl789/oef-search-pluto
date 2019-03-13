import traceback

from dap_api.src.python import DapInterface
from dap_api.src.protos import dap_description_pb2
from dap_api.src.python import SubQueryInterface
from dap_api.src.python import ProtoHelpers
from dap_api.src.python.DapInterface import DapBadUpdateRow
from dap_api.src.python import DapQueryRepn
from dap_api.src.protos import dap_update_pb2
from utils.src.python.Logging import has_logger
from dap_api.experimental.python import InMemoryDap

class AddressRegistry(InMemoryDap.InMemoryDap):
    @has_logger
    def __init__(self, name, configuration):
        super().__init__(name, configuration)

    def resolve(self, key):

        #if len(self.store) == 0:
        #    traceback.print_stack()
        #    exit(77)


        address = []
        try:
            for tblname in self.store:
                if key in self.store[tblname]:
                    for field in self.structure[tblname]:
                        address.append(self.store[tblname][key][field])
        except Exception as e:
            self.log.warn("No address entry for key: "+key.decode("utf-8")+", details: "+str(e))
            print(self.store)
        return address

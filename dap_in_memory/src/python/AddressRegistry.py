import traceback
from dap_api.src.python import DapInterface
from dap_api.src.protos import dap_description_pb2
from dap_api.src.python import SubQueryInterface
from dap_api.src.python import ProtoHelpers
from dap_api.src.python.DapInterface import DapBadUpdateRow
from dap_api.src.python import DapQueryRepn
from dap_api.src.protos import dap_update_pb2
from utils.src.python.Logging import has_logger
from dap_in_memory.src.python import InMemoryDap
from dap_api.src.protos import dap_interface_pb2


class AddressRegistry(InMemoryDap.InMemoryDap):
    @has_logger
    def __init__(self, name, configuration):
        super().__init__(name, configuration)
        self.coreToURI = {}

    def resolve(self, key):
        address = []
        try:
            for tblname in self.store:
                ckey = (key, b'')
                if ckey in self.store[tblname]:
                    for field in self.structure[tblname]:
                        address.append(self.store[tblname][ckey][field])
        except Exception as e:
            self.warning("No address entry for key: "+key.decode("utf-8")+", details: "+str(e))
            print(self.store)
        return address

    def resolveCore(self, core_name):
        result = self.coreToURI.get(core_name, None)
        if result is None:
            found = None
            for tbname in self.store:
                r = self.store[tbname].get((core_name, b''), None)
                if r is not None:
                    found = r.get("address_field", None)
                    if found is not None:
                        break
            if found is not None:
                result = found.ip + ":" + str(found.port)
                self.storeCore(core_name, result)
        return result

    def storeCore(self, core_name, uri):
        self.coreToURI[core_name] = uri

    def describe(self) -> dap_description_pb2.DapDescription:
        result = super().describe()
        del result.options[:]
        result.options.append("late")
        result.options.append("all-branches")
        return result

    def remove(self, remove_data: dap_update_pb2.DapUpdate.TableFieldValue):
        success = False
        for commit in [ False, True ]:
            upd = remove_data
            if upd:

                k, v = ProtoHelpers.decodeAttributeValueToTypeValue(upd.value)
                key = (upd.key.core, b'')

                if upd.fieldname not in self.fields:
                    raise DapBadUpdateRow("No such field", None, upd.key.core, upd.fieldname, k)
                else:
                    tbname = self.fields[upd.fieldname]["tablename"]
                    ftype = self.fields[upd.fieldname]["type"]

                if ftype != k:
                    raise DapBadUpdateRow("Bad type", tbname, upd.key.core, upd.fieldname, k)

                if commit:
                    success |= self.store[tbname][key].pop(upd.fieldname, None) is not None
        return success

    def removeAll(self, key):
        return self.store[self.tablenames[0]].pop(key, None) is not None

    def prepareConstraint(self, proto: dap_interface_pb2.ConstructQueryConstraintObjectRequest) -> dap_interface_pb2.ConstructQueryMementoResponse:
        raise Exception("AddressRegistry::prepareConstraint is NOT IMPL")

    def prepare(self, proto: dap_interface_pb2.ConstructQueryObjectRequest) -> dap_interface_pb2.ConstructQueryMementoResponse:
        r = dap_interface_pb2.ConstructQueryMementoResponse()

        if proto.operator != "result":
            r.success = False
            return r

        r.memento = b"dummy_token"
        r.success = True
        return r

    def execute(self, proto: dap_interface_pb2.DapExecute) -> dap_interface_pb2.IdentifierSequence:
        r = dap_interface_pb2.IdentifierSequence()
        r.originator = False
        for key in proto.input_idents.identifiers:
            new_result = r.identifiers.add()
            new_result.CopyFrom(key)
            addr = self.resolveCore(key.core)
            if addr:
                new_result.uri = addr

        return r

import unittest

from dap_api.src.python import DapInterface
from dap_api.experimental.python import InMemoryDap
from dap_api.src.protos import dap_update_pb2
from fetch_teams.oef_core_protocol import query_pb2

class QueryTest(unittest.TestCase):
    def setUp(self):
        """Call before every test case."""
        self.dap1 = InMemoryDap.InMemoryDap("dap1", { "wibbles": { "wibble": "string" } } );
        self.dap2 = InMemoryDap.InMemoryDap("dap2", { "wobbles": { "wobble": "string" } } );

    def tearDown(self):
        """Call after every test case."""
        pass

    def _createUpdate(self):
        update = dap_update_pb2.DapUpdate()
        newvalue = update.update.add()
        newvalue.tablename = "wibbles"
        newvalue.fieldname = "wibble"
        newvalue.value.type = 2
        newvalue.value.s = "moo"
        newvalue.key.agent_name = "007/James/Bond"
        newvalue.key.core_uri.append("localhost:10000")
        return update

    def _createQueryProto(self):
        q = py_oef_protocol_pb2.ConstraintExpr()

    def _setupAgents(self):
        for agent_name, wibble_value in [
            ("007/James/Bond", "apple"),
            ("White/Spy", "banana"),
            ("Black/Spy", "carrot"),
            ("86/Maxwell/Smart", "carrot"),
        ]:
            update = self._createUpdate()
            update.update[0].key.agent_name = agent_name
            update.update[0].value.s = wibble_value
            self.dap1.update(update)


    def testQuery(self):
        """Test case A. note that all test method names must begin with 'test.'"""
        self._setupAgents()

        q = query_pb2.Query.ConstraintExpr()

        q.constraint.attribute_name = "wibble"
        q.constraint.relation.op = 0
        q.constraint.relation.val.s = "carrot"

        dapQuery = self.dap1.makeQuery(q, "wibbles")
        results = list(self.dap1.query(dapQuery))

        assert len(results) == 2

    def testQueryOr(self):
        """Test case A. note that all test method names must begin with 'test.'"""
        self._setupAgents()

        qOr = query_pb2.Query.ConstraintExpr()
        q1 = qOr.or_.expr.add()
        q2 = qOr.or_.expr.add()

        q1.constraint.attribute_name = "wibble"
        q1.constraint.relation.op = 0
        q1.constraint.relation.val.s = "carrot"

        q2.constraint.attribute_name = "wibble"
        q2.constraint.relation.op = 0
        q2.constraint.relation.val.s = "apple"


        dapQuery = self.dap1.makeQuery(qOr, "wibbles")
        results = list(self.dap1.query(dapQuery))

        print(results)
        assert len(results) == 3

# Requires Python 3.6 and pyethereum dependencies

import unittest
import ethereum.opcodes as op
from ethereum import utils

from .generic_gas_token import TestGenericGasToken, GSLOAD, input_data_cost


class TestGST1(TestGenericGasToken):

    MINT_COST_LOWER_BOUND = op.GTXCOST + 3*op.GSTORAGEADD + 2*GSLOAD

    # Base cost of mint transaction (includes base transaction fee)
    MINT_BASE = 32259

    # Additional minting cost per token
    MINT_TOKEN_COST = 20046

    # Base cost of free transaction (includes CALL from external contract)
    FREE_BASE = 14505
    FREE_UP_TO_BASE = 14419
    FREE_FROM_BASE = 20223
    FREE_FROM_UP_TO_BASE = 20089

    # Additional free cost per token
    FREE_TOKEN_COST = 5046

    def mint_cost(self, x):
        if x == 0:
            return 21800
            
        return self.MINT_BASE + x * self.MINT_TOKEN_COST + input_data_cost(x)

    def free_cost(self, x):
        return self.FREE_BASE + x * self.FREE_TOKEN_COST + input_data_cost(x)

    def free_up_to_cost(self, x):
        return self.FREE_UP_TO_BASE + x * self.FREE_TOKEN_COST + input_data_cost(x)

    def free_from_cost(self, x):
        return self.FREE_FROM_BASE + x * self.FREE_TOKEN_COST + input_data_cost(x)

    def free_from_up_to_cost(self, x):
        return self.FREE_FROM_UP_TO_BASE + x * self.FREE_TOKEN_COST + input_data_cost(x)

    # Refund per freed token
    REFUND = op.GSTORAGEREFUND

    @classmethod
    def setUpClass(cls):
        super(TestGST1, cls).setUpClass()

        with open('contract/GST1.sol') as fd:
            contract_code = fd.read()
        cls.c = cls.s.contract(contract_code, language='solidity')
        cls.initial_state = cls.s.snapshot()

    def setUp(self):
        super().setUp()

    def get_storage(self):
        return self.s.head_state.account_to_dict(self.c.address)['storage']

    def test_ERC20_attributes(self):
        self.assertEqual(self.c.decimals(), 2)
        self.assertEqual(self.c.name(), b'Gastoken.io')
        self.assertEqual(self.c.symbol(), b'GST1')

    def test_storage(self):

        # check that storage is initially empty
        self.assertEqual(len(self.get_storage()), 0)

        # a1 mints 2
        self.assertEqual(self.c.balanceOf(self.t.a1), 0)
        self.assertIsNone(self.c.mint(2, sender=self.t.k1))
        self.assertEqual(self.c.balanceOf(self.t.a1), 2)
        self.assertEqual(self.c.totalSupply(), 2)

        # check that 4 words are stored (totalSupply, balance[a1], two mints)
        storage = self.get_storage()
        self.assertEqual(len(storage), 4)

        # free 1
        self.assertTrue(self.c.free(1, sender=self.t.k1))
        self.assertEqual(self.c.balanceOf(self.t.a1), 1)
        self.assertEqual(self.c.totalSupply(), 1)

        storage = self.get_storage()
        self.assertEqual(len(storage), 3)

        # free 1
        self.assertTrue(self.c.free(1, sender=self.t.k1))
        self.assertEqual(self.c.balanceOf(self.t.a1), 0)
        self.assertEqual(self.c.totalSupply(), 0)
        storage = self.get_storage()
        self.assertEqual(len(storage), 0)


class TestDeployedGST1(TestGST1):

    @classmethod
    def setUpClass(cls):
        super(TestDeployedGST1, cls).setUpClass()

        with open('contract/GST1.asm') as fd:
            contract_code = utils.decode_hex(fd.read())
        cls.s.head_state.set_code(cls.c.address, contract_code)
        cls.initial_state = cls.s.snapshot()

    def setUp(self):
        super().setUp()


def load_tests(loader, tests, pattern):
    full_suite = unittest.TestSuite()

    for suite in [TestDeployedGST1, TestGST1]:
        tests = loader.loadTestsFromTestCase(suite)
        full_suite.addTests(tests)
    return full_suite

if __name__ == '__main__':
    unittest.main(verbosity=2)

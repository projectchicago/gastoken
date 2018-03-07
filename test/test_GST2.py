import unittest
import ethereum.opcodes as op
from ethereum.tools.tester import k0, STARTGAS, GASPRICE, ABIContract, \
    TransactionFailed
from ethereum.exceptions import InsufficientStartGas
from ethereum.abi import ContractTranslator
from ethereum.tools._solidity import solc_parse_output, \
    solidity_get_contract_data
from ethereum import utils
import os
import subprocess

from .generic_gas_token import TestGenericGasToken, GSLOAD, GCREATE, input_data_cost
from .test_rlp import rlp_cost


def deploy_solidity_contract(contract_path, contract_name,
                             chain, sender=k0, value=0,
                             startgas=STARTGAS, gasprice=GASPRICE, *args):
    output = subprocess.check_output(
        ["solc", "--combined-json", "bin,abi", contract_path])
    result = solc_parse_output(output)
    data = solidity_get_contract_data(result, contract_path, contract_name)

    interface = data['abi']
    ct = ContractTranslator(interface)

    code = data['bin'] \
           + (ct.encode_constructor_arguments(args) if args else b'')
    addr = chain.tx(
        sender=sender,
        to=b'',
        value=value,
        data=code,
        startgas=startgas,
        gasprice=gasprice)
    return ABIContract(chain, ct, addr)


class TestGST2(TestGenericGasToken):

    # hex version of child contract binary (runtime component without initcode)
    CHILD_CONTRACT_BIN = "6eb3f879cb30fe243b4dfee438691c043318585733ff"

    # length in bytes of the contract deployed when minting a token
    CONTRACT_LEN = len(CHILD_CONTRACT_BIN) // 2

    # approx cost of MINT
    MINT_COST_LOWER_BOUND = op.GTXCOST + 2 * op.GSTORAGEADD + 2 * GSLOAD \
                            + GCREATE + op.GCONTRACTBYTE * CONTRACT_LEN

    # Base cost of mint transaction (includes base transaction fee)
    MINT_BASE = 32254

    # Additional minting cost per token
    MINT_TOKEN_COST = 36543

    # Base cost of free transaction (includes CALL from external contract)
    FREE_BASE = 14154
    FREE_UP_TO_BASE = 14053
    FREE_FROM_BASE = 19809
    FREE_FROM_UP_TO_BASE = 19664

    # min-max estimated costs for the `mk_contract_address` function that
    # produces an RLP encoding of the nonce and address
    RLP_LOWER_BOUND = rlp_cost(1)
    RLP_UPPER_BOUND = rlp_cost(256**9-1)

    # Upper bound on the additional free cost per token.
    # For small values of nonce ( 1 <= nonce <= 127 ), the cost is exactly 6228
    # gas.
    # As an upper bound, we add the difference in costs of the most expensive
    # nonce to RLP Encode (nonce = 256**9 - 1) and the least expensive
    # (nonce = 1). This difference seems to be 642 gas.
    FREE_TOKEN_COST = 6870

    def nth_child_addr(self, n):
        a = utils.encode_hex(utils.mk_contract_address(self.c.address, n))
        return a

    def nth_child_has_code(self, n):
        return len(self.s.head_state.get_code(self.nth_child_addr(n))) > 0

    def mint_cost(self, x):
        return self.MINT_BASE + x * self.MINT_TOKEN_COST + input_data_cost(x)

    def _free_cost(self, base, token, x):
        if x == 0:
            return (base - 10 + input_data_cost(x), base + 10 + input_data_cost(x))

        low = base + x * (token - self.RLP_UPPER_BOUND + self.RLP_LOWER_BOUND) + input_data_cost(x)
        high = base + x * token + input_data_cost(x)
        return (low, high)

    def free_cost(self, x):
        return self._free_cost(self.FREE_BASE, self.FREE_TOKEN_COST, x)

    def free_up_to_cost(self, x):
        return self._free_cost(self.FREE_UP_TO_BASE, self.FREE_TOKEN_COST, x)

    def free_from_cost(self, x):
        return self._free_cost(self.FREE_FROM_BASE, self.FREE_TOKEN_COST, x)

    def free_from_up_to_cost(self, x):
        return self._free_cost(self.FREE_FROM_UP_TO_BASE, self.FREE_TOKEN_COST, x)

    # Refund per freed token
    REFUND = op.GSUICIDEREFUND

    @classmethod
    def deploy(cls, contract_path):
        cwd = os.getcwd()
        os.chdir('contract')

        # Our ContractGasToken contract relies on being deployed at address
        # 0x0000000000b3F879cb30FE243b4Dfee438691c04
        # Through magic, we have determined that a contract created in a
        # transaction with nonce == magic_nonce sent from
        # address == magic_address will have this address.
        magic_key = 0xa7d79a51ff835c80c1f5c2c3b350b15f95550e41e379e50a10ef2ff3f6a215aa
        magic_address = 0x470F1C3217A2F408769bca5AB8a5c67A9040664A
        magic_nonce = 125
        contract_address = 0x0000000000b3F879cb30FE243b4Dfee438691c04

        computed_address = int(utils.encode_hex(utils.mk_contract_address(magic_address, magic_nonce)), 16)
        assert (computed_address == contract_address)

        cls.s.head_state.set_nonce(magic_address, magic_nonce)

        # check that we have reached magic_nonce and that there is no code at magic_address
        assert (cls.s.head_state.get_nonce(magic_address) == magic_nonce)
        assert (0 == len(cls.s.head_state.get_code(contract_address)))

        # deploy contract and check that it has been deployed successfully
        cls.c = deploy_solidity_contract(contract_path,
                                         'GasToken2',
                                         cls.s,
                                         sender=magic_key)
        assert (0 < len(cls.s.head_state.get_code(contract_address)))
        os.chdir(cwd)

    @classmethod
    def setUpClass(cls):
        super(TestGST2, cls).setUpClass()

        cls.deploy('GST2_ETH.sol')
        cls.initial_state = cls.s.snapshot()

    def setUp(self):
        super().setUp()

    def get_storage(self):
        return self.s.head_state.account_to_dict(self.c.address)['storage']

    def test_ERC20_attributes(self):
        self.assertEqual(self.c.decimals(), 2)
        self.assertEqual(self.c.name(), b'Gastoken.io')
        self.assertEqual(self.c.symbol(), b'GST2')

    def test_storage_and_contracts(self):

        num_deployed_contracts = len(self.s.head_state.to_dict().keys())

        # check nonce
        self.assertEqual(self.s.head_state.get_nonce(self.c.address), 1)

        # check that storage is initially empty
        self.assertEqual(len(self.get_storage()), 0)

        # a1 mints 2
        self.assertEqual(self.c.balanceOf(self.t.a1), 0)
        self.assertIsNone(self.c.mint(2, sender=self.t.k1))
        self.assertEqual(self.c.balanceOf(self.t.a1), 2)
        self.assertEqual(self.c.totalSupply(), 2)

        # check that 2 words are stored (balance[a1], head)
        storage = self.get_storage()
        self.assertEqual(len(storage), 2)

        # check that two contracts were created
        a1 = utils.encode_hex(utils.mk_contract_address(self.c.address, 1))
        a2 = utils.encode_hex(utils.mk_contract_address(self.c.address, 2))

        self.assertEqual(len(self.s.head_state.to_dict().keys()),
                         num_deployed_contracts + 2)

        self.assertTrue(a1 in self.s.head_state.to_dict().keys())
        self.assertTrue(a2 in self.s.head_state.to_dict().keys())

        code1 = utils.encode_hex(self.s.head_state.get_code(a1))
        self.assertEqual(code1, self.CHILD_CONTRACT_BIN)

        code2 = utils.encode_hex(self.s.head_state.get_code(a2))
        self.assertEqual(code2, self.CHILD_CONTRACT_BIN)

        # free 1
        self.assertTrue(self.c.free(1, sender=self.t.k1))
        self.assertEqual(self.c.balanceOf(self.t.a1), 1)
        self.assertEqual(self.c.totalSupply(), 1)

        # check that 2 words are stored (balance[a1], head, tail)
        storage = self.get_storage()
        self.assertEqual(len(storage), 3)

        # check that a contract was killed
        self.assertEqual(len(self.s.head_state.to_dict().keys()),
                         num_deployed_contracts + 1)
        self.assertFalse(a1 in self.s.head_state.to_dict().keys())
        self.assertTrue(a2 in self.s.head_state.to_dict().keys())

        # free 1
        self.assertTrue(self.c.free(1, sender=self.t.k1))
        self.assertEqual(self.c.balanceOf(self.t.a1), 0)
        self.assertEqual(self.c.totalSupply(), 0)

        # check that 2 words are stored (head, tail)
        storage = self.get_storage()
        self.assertEqual(len(storage), 2)

        # check that a contract was killed
        self.assertEqual(len(self.s.head_state.to_dict().keys()),
                         num_deployed_contracts)
        self.assertFalse(a1 in self.s.head_state.to_dict().keys())
        self.assertFalse(a2 in self.s.head_state.to_dict().keys())

    def test_gst2_eth_example_free(self):
        # Create contract
        os.chdir('contract')
        example_contract = deploy_solidity_contract(
            'gst2_free_example.sol',
            'GST2FreeExample',
            self.s,
            sender=self.t.k0)
        os.chdir('..')

        # Intial mint and free to set storage to non-zero values
        self.assertFalse(self.nth_child_has_code(1))
        self.assertIsNone(self.c.mint(1))
        self.assertTrue(self.nth_child_has_code(1))
        self.assertTrue(self.c.free(1))
        self.assertFalse(self.nth_child_has_code(1))

        # Supply example_contract with some tokens
        self.assertIsNone(self.c.mint(50))
        self.assertTrue(self.c.transfer(example_contract.address, 50))
        self.assertEqual(50, self.c.balanceOf(example_contract.address))

        # Free with varying gas amounts to check that we never destroy tokens without
        # self-destructing a contract.
        tail_nonce = 2
        for gas in range(24000, 1000000, 1000):
            old_balance = self.c.balanceOf(example_contract.address)
            freed = example_contract.freeExample(180, startgas=gas)
            print('Freed', freed, 'with', gas, 'gas')
            self.assertEqual(old_balance - freed, self.c.balanceOf(example_contract.address))
            tail_nonce += freed
            self.assertFalse(self.nth_child_has_code(tail_nonce - 1))
            self.assertTrue(self.nth_child_has_code(tail_nonce))

            # Replenish example_contract's suply
            while self.c.balanceOf(example_contract.address) < 200:
                self.assertIsNone(self.c.mint(50))
                self.assertTrue(self.c.transfer(example_contract.address, 50))

    def test_gst2_eth_example_freeFrom(self):
        # Create contract
        os.chdir('contract')
        example_contract = deploy_solidity_contract(
            'gst2_free_example.sol',
            'GST2FreeExample',
            self.s,
            sender=self.t.k0)
        os.chdir('..')

        # Intial mint and free to set storage to non-zero values
        self.assertFalse(self.nth_child_has_code(1))
        self.assertIsNone(self.c.mint(1))
        self.assertTrue(self.nth_child_has_code(1))
        self.assertTrue(self.c.free(1))
        self.assertFalse(self.nth_child_has_code(1))

        # Supply example_contract with some tokens
        self.assertIsNone(self.c.mint(60))
        self.assertTrue(self.c.approve(example_contract.address, 1000000000))
        self.assertEqual(60, self.c.balanceOf(self.t.a0))
        self.assertEqual(1000000000, self.c.allowance(self.t.a0, example_contract.address))

        # Free with varying gas amounts to check that we never destroy tokens without
        # self-destructing a contract.
        tail_nonce = 2
        for gas in range(24000, 1000000, 1000):
            old_balance = self.c.balanceOf(self.t.a0)
            freed = example_contract.freeFromExample(self.t.a0, 180, startgas=gas)
            print('Freed', freed, 'with', gas, 'gas')
            self.assertEqual(old_balance - freed, self.c.balanceOf(self.t.a0))
            tail_nonce += freed
            self.assertFalse(self.nth_child_has_code(tail_nonce - 1))
            self.assertTrue(self.nth_child_has_code(tail_nonce))

            # Replenish example_contract's suply
            while self.c.balanceOf(self.t.a0) < 200:
                self.assertIsNone(self.c.mint(50))

    def test_solidity_compiler_bug(self):
        self.assertFalse(self.nth_child_has_code(1))

        self.assertIsNone(self.c.mint(18, sender=self.t.k1))
        self.assertEqual(self.c.totalSupply(), 18)

        self.assertTrue(self.nth_child_has_code(1))

        self.assertTrue(self.c.free(1, sender=self.t.k1))
        self.assertEqual(self.c.totalSupply(), 17)

        self.assertFalse(self.nth_child_has_code(1))
        self.assertTrue(self.nth_child_has_code(2))
        self.assertTrue(self.nth_child_has_code(3))

        self.assertEqual(True, self.c.free(2, sender=self.t.k1, startgas=65000 - 17000 + 700))

        # Due to the bug, the second child wasn't destroyed
        self.assertTrue(self.nth_child_has_code(2))
        self.assertFalse(self.nth_child_has_code(3))

    def test_child_initcode(self):
        """Check that the initcode of the child contract creates the correct
        contract.
        """
        child_address = utils.mk_contract_address(self.c.address, 1)
        self.assertEqual(b'', self.s.head_state.get_code(child_address))
        self.c.mint(1)
        self.assertEqual(self.CHILD_CONTRACT_BIN, utils.encode_hex(
            self.s.head_state.get_code(child_address)))

    def test_child_address_check(self):
        """Check that the child contract will throw when it's called by anybody
        except the ERC20 contract.
        """
        child_address = utils.mk_contract_address(self.c.address, 1)
        self.c.mint(1)
        self.assertLess(0, len(self.s.head_state.get_code(child_address)))
        with self.assertRaises(TransactionFailed):
            self.s.tx(
                sender=self.t.k0,
                to=child_address,
                value=0,
                data=b'',
                startgas=10 ** 20)

    def test_mint_oog(self):
        """ Check that mint(1) either fully succeeds (a new child contract is
        created and balances are increased) or fails with OOG and reverts all
        changes
        """

        def get_all_contracts():
            # ignore weird coinbase address that Pyethreum sometimes
            # randomly throws in
            CB = "3535353535353535353535353535353535353535"
            d = list(self.s.head_state.to_dict().keys())
            if CB in d:
                d.remove(CB)
            return d

        original_contracts = get_all_contracts()
        num_deployed_contracts = len(original_contracts)

        # check original nonce
        tot_minted = 0
        self.assertEqual(self.s.head_state.get_nonce(self.c.address), tot_minted + 1)

        # mint one token to already get the storage values in place
        self.assertIsNone(self.c.mint(1, sender=self.t.k1))
        tot_minted += 1

        # check original nonce
        self.assertEqual(self.s.head_state.get_nonce(self.c.address), tot_minted + 1)

        min_gas = 0
        max_gas = 2**20

        # mint(1) with max_gas should succeed
        self.assertIsNone(self.c.mint(1, sender=self.t.k1, startgas=max_gas))
        tot_minted += 1

        # check balance
        self.assertEqual(self.c.balanceOf(self.t.a1), tot_minted)
        self.assertEqual(self.c.totalSupply(), tot_minted)

        # check new nonce and created contract
        a = utils.encode_hex(utils.mk_contract_address(self.c.address, tot_minted))
        self.assertEqual(self.s.head_state.get_nonce(self.c.address), tot_minted + 1)
        self.assertEqual(len(get_all_contracts()), num_deployed_contracts + tot_minted)
        self.assertTrue(a in get_all_contracts())

        # mint(1) with min_gas should fail
        self.assertRaises(InsufficientStartGas, lambda: self.c.mint(1, sender=self.t.k1, startgas=min_gas))

        # check balance didn't change
        self.assertEqual(self.c.balanceOf(self.t.a1), tot_minted)
        self.assertEqual(self.c.totalSupply(), tot_minted)

        # check nonce and number of contracts didn't change
        self.assertEqual(self.s.head_state.get_nonce(self.c.address), tot_minted + 1)
        self.assertEqual(len(get_all_contracts()), num_deployed_contracts + tot_minted)

        # search for the minimal amount of gas for a mint(1) call to succeed
        while max_gas - min_gas > 1:
            gas = int((max_gas + min_gas)/2)
            try:
                self.assertIsNone(self.c.mint(1, sender=self.t.k1, startgas=gas))
                print("\tmint(1) succeeded with {} gas\t (nonce={})".format(gas, self.s.head_state.get_nonce(self.c.address)))
                tot_minted += 1
                max_gas = gas

                # make sure we created a child at the right address
                a = utils.encode_hex(utils.mk_contract_address(self.c.address, tot_minted))
                self.assertTrue(a in get_all_contracts())
                self.assertTrue(utils.encode_hex(self.s.head_state.get_code(a)) == self.CHILD_CONTRACT_BIN)

            except (TransactionFailed, InsufficientStartGas):
                print("\tmint(1) failed with {} gas\t\t (nonce={})".format(gas, self.s.head_state.get_nonce(self.c.address)))

                # make sure the child was not created
                a = utils.encode_hex(utils.mk_contract_address(self.c.address, tot_minted + 1))
                self.assertTrue(a not in get_all_contracts() or self.s.head_state.get_code(a) == b'')
                min_gas = gas

            # check balance agrees with tot_minted
            self.assertEqual(self.c.balanceOf(self.t.a1), tot_minted)
            self.assertEqual(self.c.totalSupply(), tot_minted)

            # check nonce and number of contracts agree with tot_minted
            self.assertEqual(self.s.head_state.get_nonce(self.c.address), tot_minted + 1)
            self.assertEqual(len(get_all_contracts()), num_deployed_contracts + tot_minted)

        print(max_gas, min_gas)
        self.assertIsNone(self.c.mint(1, sender=self.t.k1, startgas=max_gas))
        self.assertRaises(TransactionFailed, lambda: self.c.mint(1, sender=self.t.k1, startgas=min_gas))


class TestDeployedGST2(TestGST2):

    @classmethod
    def setUpClass(cls):
        super(TestDeployedGST2, cls).setUpClass()

        with open('contract/GST2_ETH.asm') as fd:
            contract_code = utils.decode_hex(fd.read())
        cls.s.head_state.set_code(cls.c.address, contract_code)

        cls.initial_state = cls.s.snapshot()

    def setUp(self):
        super().setUp()


class TestGST2ETC(TestGST2):

    @classmethod
    def setUpClass(cls):
        super(TestGST2, cls).setUpClass()
        cls.deploy('GST2_ETC.sol')
        cls.initial_state = cls.s.snapshot()

    def setUp(self):
        super().setUp()

    @unittest.skip("This bug is fixed in GST2 deployed on ETC")
    def test_gst2_eth_example_free(self):
        pass

    @unittest.skip("This bug is fixed in GST2 deployed on ETC")
    def test_gst2_eth_example_freeFrom(self):
        pass

    @unittest.skip("This bug is fixed in GST2 deployed on ETC")
    def test_solidity_compiler_bug(self):
        pass

    def test_solidity_compiler_bug_workaround(self):
        self.assertFalse(self.nth_child_has_code(1))

        self.assertIsNone(self.c.mint(18, sender=self.t.k1))
        self.assertEqual(self.c.totalSupply(), 18)

        self.assertTrue(self.nth_child_has_code(1))

        self.assertTrue(self.c.free(1, sender=self.t.k1))
        self.assertEqual(self.c.totalSupply(), 17)

        self.assertFalse(self.nth_child_has_code(1))
        self.assertTrue(self.nth_child_has_code(2))
        self.assertTrue(self.nth_child_has_code(3))

        self.assertEqual(True, self.c.free(2, sender=self.t.k1, startgas=65000 - 17000 + 700))

        # We have a working workaround, the second child was destroyed
        self.assertFalse(self.nth_child_has_code(2))
        self.assertFalse(self.nth_child_has_code(3))



class TestDeployedGST2ETC(TestGST2ETC):

    @classmethod
    def setUpClass(cls):
        super(TestDeployedGST2ETC, cls).setUpClass()

        with open('contract/GST2_ETC.asm') as fd:
            contract_code = utils.decode_hex(fd.read())
        cls.s.head_state.set_code(cls.c.address, contract_code)

        cls.initial_state = cls.s.snapshot()

    def setUp(self):
        super().setUp()


def load_tests(loader, tests, pattern):
    full_suite = unittest.TestSuite()

    for suite in [TestDeployedGST2, TestGST2, TestDeployedGST2ETC, TestGST2ETC]:
        tests = loader.loadTestsFromTestCase(suite)
        full_suite.addTests(tests)
    return full_suite


if __name__ == '__main__':
    unittest.main(verbosity=2)

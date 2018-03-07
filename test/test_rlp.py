from ethereum.tools import tester
from ethereum import utils
import unittest
import random
from itertools import chain
from .generic_gas_token import input_data_cost
import warnings

RLP_BASE = 21000


# Cost of calling the mk_contract_address function for a given nonce.
# The value returned includes the cost of traversing the function jump table.
# These values are best used to compute the delta in gas costs as the nonce 
# increases. We find that rlp_cost(256**9 - 1) - rlp_cost(1) = 1526 - 884 = 642
def rlp_cost(nonce):
    if nonce == 0:
        return 1036
    elif nonce <= 127:
        return 906
    else:
        hex = utils.encode_hex(utils.encode_int(nonce))
        num_bytes = len(hex) / 2
        cost = 1058 + num_bytes * 60
        if nonce >= 256**8:
            cost -= 50
        return cost


class TestRLP(unittest.TestCase):

    t = None
    s = None
    c = None

    @classmethod
    def setUpClass(cls):
        super(TestRLP, cls).setUpClass()

        # Initialize tester, contract and expose relevant objects
        cls.t = tester
        cls.s = cls.t.Chain()

        cls.s.head_state.gas_limit = 10**80
        cls.s.head_state.set_balance(cls.t.a0, 10**80)
        cls.s.head_state.set_balance(cls.t.a1, 10**80)
        cls.s.head_state.set_balance(cls.t.a2, 10**80)
        cls.s.head_state.set_balance(cls.t.a3, 10**80)

        with open('contract/rlp.sol') as fd:
            contract_code = fd.read()
            contract_code = contract_code.replace(" pure internal ", " public ")
        cls.c = cls.s.contract(contract_code, language='solidity')
        cls.initial_state = cls.s.snapshot()

    def tot_rlp_cost(self, nonce, address):
        cost = RLP_BASE + rlp_cost(nonce)
        cost += input_data_cost(nonce)

        if isinstance(address, str):
            cost += input_data_cost(utils.decode_int(utils.decode_hex(address)), num_bytes=20)
        else:
            cost += input_data_cost(address, num_bytes=20)
        return cost

    def test_rlp(self):
        addresses = [utils.encode_hex(self.c.address), 0x0, "{:x}".format(256**20-1)]
        nonces = [0,
                  1, 2, 5, 10, 20, 50, 100, 127, 128,
                  129, 255, 256, 257, 500, 1000, 256**2-1,
                  256**2, 256**2+256+1, 256**3-1,
                  256**3, 256**3+256**2+256+1, 256**4-1,
                  256**5-1,
                  256**6-1,
                  256**7-1,
                  256**8-1,
                  256**8, 256**8+1, 256**8 + 256**7 + 256**6 + 256**5 + 256**4 + 256**3+ 256**2 + 256 + 1, 256**9-2,
                  256**9-1]

        scaled_as_expected = True
        for address in addresses:
            for nonce in nonces:
                print("a={}, n={}".format(address, nonce))

                gas_used_before = self.s.head_state.gas_used
                a1 = self.c.mk_contract_address(address, nonce)
                gas_used_after = self.s.head_state.gas_used

                gas_used = gas_used_after - gas_used_before
                expected = self.tot_rlp_cost(nonce, address)

                if gas_used != expected:
                    scaled_as_expected = False
                    warnings.warn("RLP({}, {}) did not scale as expected. Got {}. "
                                  "Expected {}".format(nonce, address, gas_used, expected))

                a2 = "0x{}".format(utils.encode_hex(
                    utils.mk_contract_address(address, nonce)
                ))

                self.assertEqual(a1, a2)

        self.assertTrue(scaled_as_expected)

    def test_exhaustive1(self):
        addresses = [
            b'\x00' * 20,
            b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19',
            b'\xff\xfe\xfd\xfc\xfb\xfa\xf9\xf8\xf7\xf7\xf6\xf5\xf4\xf3\xf2\x00\xf0\x53\x00\x00',
        ]
        for address in addresses:
            for nonce in range(1025):
                self.assertEqual(utils.encode_hex(utils.mk_contract_address(address, nonce)), self.c.mk_contract_address(address, nonce)[2:])

    def test_exhaustive2(self):
        # This is the actual address we use on the mainnet
        address = utils.normalize_address("0x0000000000b3F879cb30FE243b4Dfee438691c04")
        for nonce in chain(range(72000), range(4722366482869645213696-72000, 4722366482869645213696)):
            self.assertEqual(utils.encode_hex(utils.mk_contract_address(address, nonce)), self.c.mk_contract_address(address, nonce)[2:])
            if nonce % 1000 == 0:
                print('exhaustive test currently at nonce:', nonce)

    def test_random(self):
        for i in range(20):
            address = random_address()
            print('testing 200 random nonces for address {}'.format(utils.encode_hex(address)))
            for i in range(200):
                nonce = random.randint(0, 4722366482869645213696)
                self.assertEqual(utils.encode_hex(utils.mk_contract_address(address, nonce)), self.c.mk_contract_address(address, nonce)[2:])


def random_address():
    address = [0] * 20
    for i in range(20):
        address[i] = random.randint(0, 255)
    return bytes(address)

if __name__ == '__main__':
    unittest.main(verbosity=2)

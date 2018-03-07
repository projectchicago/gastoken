
from .generic_ERC20_token import TestGenericERC20Token
import ethereum.opcodes as op
import collections
import warnings

# cost of SLOAD op (200), CALL op (700) and CREATE op (24000)
GSLOAD = op.opcodes[op.reverse_opcodes['SLOAD']][-1] + op.SLOAD_SUPPLEMENTAL_GAS
GCALL = op.opcodes[op.reverse_opcodes['CALL']][-1] + op.CALL_SUPPLEMENTAL_GAS
GCREATE = op.opcodes[op.reverse_opcodes['CREATE']][-1]


def input_data_cost(x, num_bytes=32):
    bytez = tuple((x).to_bytes(num_bytes, byteorder='big'))
    zero_bytes = sum([1 for b in bytez if b == 0])

    # 4 for zero bytes, 68 for non-zero
    return op.GTXDATAZERO * zero_bytes + \
           op.GTXDATANONZERO * (len(bytez) - zero_bytes)


class TestGenericGasToken(TestGenericERC20Token):

    MINT_COST_LOWER_BOUND = None
    REFUND = None

    def mint_cost(self, x):
        pass

    def free_cost(self, x):
        pass

    def free_up_to_cost(self, x):
        pass

    def free_from_cost(self, x):
        pass

    def free_from_up_to_cost(self, x):
        pass

    @classmethod
    def setUpClass(cls):
        super(TestGenericGasToken, cls).setUpClass()

        with open('contract/test_helper.sol') as fd:
            helper_contract_code = fd.read()
        cls.helper = cls.s.contract(helper_contract_code, language='solidity')

    def setUp(self):
        super().setUp()

    def test_abi(self):
        self.assertEqual(
            set(self.c.translator.function_data.keys()),
            {'name', 'approve', 'totalSupply', 'transferFrom', 'decimals',
             'balanceOf', 'symbol', 'mint', 'transfer', 'free', 'allowance',
             'freeUpTo', 'freeFrom', 'freeFromUpTo'})

    def test_freeFrom(self):

        def freeFrom(address_from, amount, address_spender, key_spender):
            original_balance = self.c.balanceOf(address_from)
            original_allowance = self.c.allowance(address_from, address_spender)
            self.assertTrue(self.c.freeFrom(address_from, amount, sender=key_spender))
            self.assertEqual(original_balance - amount, self.c.balanceOf(address_from))
            self.assertEqual(original_allowance - amount, self.c.allowance(address_from, address_spender))

        freeFrom(self.t.a0, 0, self.t.a1, self.t.k1)
        self.c.mint(20, sender=self.t.k0)
        self.c.approve(self.t.a1, 10)
        freeFrom(self.t.a0, 0, self.t.a1, self.t.k1)
        freeFrom(self.t.a0, 1, self.t.a1, self.t.k1)
        freeFrom(self.t.a0, 4, self.t.a1, self.t.k1)
        freeFrom(self.t.a0, 5, self.t.a1, self.t.k1)
        self.assertFalse(self.c.freeFrom(self.t.a0, 1))
        self.c.approve(self.t.a1, 10)
        freeFrom(self.t.a0, 10, self.t.a1, self.t.k1)
        freeFrom(self.t.a0, 0, self.t.a1, self.t.k1)
        self.assertFalse(self.c.freeFrom(self.t.a0, 1))
        self.c.approve(self.t.a1, 10)
        self.assertFalse(self.c.freeFrom(self.t.a0, 1))
        self.c.mint(10, sender=self.t.k0)
        freeFrom(self.t.a0, 10, self.t.a1, self.t.k1)
        self.assertEqual(0, self.c.balanceOf(self.t.a0))
        self.assertEqual(0, self.c.allowance(self.t.a0, self.t.a1))

    def test_freeUpTo(self):

        self.assertEqual(0, self.c.balanceOf(self.t.a0))
        self.c.mint(20, sender=self.t.k0)
        self.assertEqual(20, self.c.balanceOf(self.t.a0))
        self.assertEqual(0, self.c.freeUpTo(0))
        self.assertEqual(20, self.c.balanceOf(self.t.a0))
        self.assertEqual(1, self.c.freeUpTo(1))
        self.assertEqual(19, self.c.balanceOf(self.t.a0))
        self.assertEqual(19, self.c.freeUpTo(20))
        self.assertEqual(0, self.c.balanceOf(self.t.a0))
        self.assertEqual(0, self.c.freeUpTo(100))

    def test_freeFromUpTo(self):

        def freeFromUpTo(address_from, amount, address_spender, key_spender):
            original_balance = self.c.balanceOf(address_from)
            original_allowance = self.c.allowance(address_from, address_spender)
            expected_freed = min([original_allowance, original_balance, amount])
            self.assertEqual(expected_freed, self.c.freeFromUpTo(address_from, amount, sender=key_spender))
            self.assertEqual(original_balance - expected_freed, self.c.balanceOf(address_from))
            self.assertEqual(original_allowance - expected_freed, self.c.allowance(address_from, address_spender))

        freeFromUpTo(self.t.a0, 0, self.t.a1, self.t.k1)
        freeFromUpTo(self.t.a0, 10, self.t.a1, self.t.k1)
        self.c.mint(20, sender=self.t.k0)
        self.c.approve(self.t.a1, 9, sender=self.t.k0)
        freeFromUpTo(self.t.a0, 0, self.t.a1, self.t.k1)
        freeFromUpTo(self.t.a0, 1, self.t.a1, self.t.k1)
        freeFromUpTo(self.t.a0, 9, self.t.a1, self.t.k1)
        self.c.approve(self.t.a1, 10, sender=self.t.k0)
        freeFromUpTo(self.t.a0, 10, self.t.a1, self.t.k1)
        freeFromUpTo(self.t.a0, 10, self.t.a1, self.t.k1)
        self.c.mint(20, sender=self.t.k0)
        self.c.approve(self.t.a1, 1000, sender=self.t.k0)
        freeFromUpTo(self.t.a0, 20, self.t.a1, self.t.k1)

    def test_mint_scaling(self):
        # make a call that initializes totalSupply and balance[a1]
        gas_used_before = self.s.head_state.gas_used
        self.assertIsNone(self.c.mint(1, sender=self.t.k1, startgas=10 ** 20))
        gas_used = self.s.head_state.gas_used - gas_used_before

        cost_lower_bound = self.MINT_COST_LOWER_BOUND
        cost_upper_bound = cost_lower_bound + 2000

        self.assertTrue(cost_lower_bound <= gas_used <= cost_upper_bound)

        mints = [0,                                                 # 0 non-zero byte
                 1, 2, 3, 4, 5, 10, 20, 50, 100, 255, 256, 256**2,  # 1 non-zero byte
                 257, 500, 1000, 256**2 + 1,                        # 2 non-zero bytes
                 256**2 + 256 + 1]                                  # 3 non-zero bytes

        expected_balance = 1
        scaled_as_expected = True

        print()
        for i in mints:
            print("\tminting {} tokens".format(i))
            expected_balance += i

            gas_used_before = self.s.head_state.gas_used
            self.assertIsNone(
                self.c.mint(i, sender=self.t.k1, startgas=10 ** 20))
            gas_used = self.s.head_state.gas_used - gas_used_before

            expected = self.mint_cost(i)
            as_expected = -0.01 <= ((gas_used - expected) / expected) <= 0.01

            if not as_expected:
                scaled_as_expected = False
                warnings.warn("Mint({}) did not scale as expected. Got {}. "
                              "Expected {}".format(i, gas_used, expected))

            self.assertEqual(self.c.totalSupply(), expected_balance)
            self.assertEqual(self.c.balanceOf(self.t.a1), expected_balance)

        self.assertTrue(scaled_as_expected)

    def test_free_cost_and_refund(self):
        """Check that the various free* methods actually refund the correct
        amount of gas and that the cost of freeing x tokens is roughly linear
        in x.

        Since we can only get a refund up to half of the total tx cost, we use
        a helper contract that burns a large amount of gas before calling free.
        This will cause the transaction to always consume at least 2x the refunded
        amount and will thus be able to detect the full refund.
        """

        free_amounts =\
            [0,                                                 # 0 non-zero byte
             1, 2, 3, 4, 5, 10, 20, 50, 100, 255, 256, 256**2,  # 1 non-zero byte
             257, 500, 1000]

        # we can only get a refund up to half the transaction price
        ideal_burn = max(free_amounts) * self.REFUND * 2 + 1000

        TestCase = collections.namedtuple(
            'TestCase', 'name fn needs_transfer cost_fn')

        if self.c.freeUpTo is None:
            test_cases = [
                TestCase('free', self.helper.burnGasAndFree, True,
                         self.free_cost)
            ]
        else:
            test_cases = [
                TestCase('free', self.helper.burnGasAndFree, True,
                         self.free_cost),
                TestCase('freeUpTo', self.helper.burnGasAndFreeUpTo, True,
                         self.free_up_to_cost),
                TestCase('freeFrom', self.helper.burnGasAndFreeFrom, False,
                         self.free_from_cost),
                TestCase('freeFromUpTo', self.helper.burnGasAndFreeFromUpTo, False,
                         self.free_from_up_to_cost),
            ]

        # gas cost changes after 256 tokens due to having two non-zero bytes
        self.c.mint(256,
                    sender=self.t.k1,
                    startgas=10 ** 20)
        self.assertTrue(self.c.free(256,
                                    sender=self.t.k1))

        # Determine how much gas is actually burned by burnGas(ideal_burn)
        gas_used_before_burn = self.s.head_state.gas_used
        self.assertIsNone(self.helper.burnGas(ideal_burn,
                                              startgas=10 ** 20))
        actual_burn = self.s.head_state.gas_used - gas_used_before_burn
        self.assertLessEqual(ideal_burn, actual_burn)

        # Approve helper contract to spend (almost) infinite amounts of tokens
        self.assertTrue(self.c.approve(self.helper.address, 2 ** 128,
                                       sender=self.t.k1))

        print()
        for test_case in test_cases:
            with self.subTest(name=test_case.name):

                # mint tokens required for test case and transfer them to
                # the helper contract if the test case requires it
                self.c.mint(sum(free_amounts) + 10,
                            sender=self.t.k1,
                            startgas=10**20)
                if test_case.needs_transfer:
                    self.assertTrue(self.c.transfer(self.helper.address,
                                                    sum(free_amounts) + 1,
                                                    sender=self.t.k1))

                scaled_as_expected = True
                # record cost and check expected refund for each free_amount
                for free_amount in free_amounts:
                    print("\tfreeing {} tokens".format(free_amount))
                    gas_used_before = self.s.head_state.gas_used
                    refund = self.get_refund_from_tx(
                        lambda: test_case.fn(self.c.address, ideal_burn,
                                             free_amount,
                                             sender=self.t.k1,
                                             startgas=10 ** 20))

                    expected = test_case.cost_fn(free_amount)
                    gas_used = self.s.head_state.gas_used - gas_used_before - actual_burn + refund

                    print(gas_used, expected)

                    if isinstance(expected, tuple):
                        as_expected = (expected[0] <= gas_used <= expected[1])
                    else:
                        as_expected = -0.01 <= ((gas_used - expected) / expected) <= 0.01

                    if not as_expected:
                        scaled_as_expected = False
                        warnings.warn("{}({}) did not scale as expected. Got {}. "
                                      "Expected {}".format(test_case.name, free_amount, gas_used, expected))

                    self.assertEqual(free_amount * self.REFUND, refund)

                self.assertTrue(scaled_as_expected)

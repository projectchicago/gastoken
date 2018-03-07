# Requires Python 3.6 and pyethereum dependencies

import unittest
from ethereum.tools import tester
from ethereum import utils


def bytes_to_int(bytez):
    o = 0
    for b in bytez:
        o = o * 256 + b
    return o


class TestGenericERC20Token(unittest.TestCase):

    t = None
    s = None
    c = None

    transfer_topic = bytes_to_int(utils.sha3("Transfer(address,address,uint256)"))
    approval_topic = bytes_to_int(utils.sha3("Approval(address,address,uint256)"))

    @classmethod
    def setUpClass(cls):
        super(TestGenericERC20Token, cls).setUpClass()

        # Initialize tester, contract and expose relevant objects
        cls.t = tester
        cls.s = cls.t.Chain()

        cls.s.head_state.gas_limit = 10**80
        cls.s.head_state.set_balance(cls.t.a0, 10**80)
        cls.s.head_state.set_balance(cls.t.a1, 10**80)
        cls.s.head_state.set_balance(cls.t.a2, 10**80)
        cls.s.head_state.set_balance(cls.t.a3, 10**80)

        cls.initial_state = cls.s.snapshot()

    def setUp(self):
        self.s.revert(self.initial_state)

    def get_refund_from_tx(self, func):
        from ethereum.slogging import get_logger
        log_tx = get_logger('eth.pb.tx')
        log_msg_prefix = 'DEBUG:eth.pb.tx:Refunding gas_refunded='

        with self.assertLogs(log_tx, "DEBUG") as cm:
            func()

            refund_log = [log_msg for log_msg in cm.output
                          if log_msg.startswith(log_msg_prefix)]

            if len(refund_log) == 0:
                refund = 0
            else:
                refund = int(refund_log[0].split(log_msg_prefix)[1])
            return refund

    def assert_tx_failed(self, function_to_test,
                         exception=tester.TransactionFailed):
        """
        Ensure that transaction fails, reverting state
        (to prevent gas exhaustion)
        """
        initial_state = self.s.snapshot()
        self.assertRaises(exception, function_to_test)
        self.s.revert(initial_state)

    def check_logs(self, topics, data):
        found = False
        for log_entry in self.s.head_state.receipts[-1].logs:
            if topics == log_entry.topics and data == log_entry.data:
                found = True
                if not found:
                    self.fail(msg="Expected log not found in last log entry.")

        self.assertTrue(found)

    def test_abi(self):
        self.assertEqual(
            set(self.c.translator.function_data.keys()),
            {'name', 'approve', 'totalSupply', 'transferFrom', 'decimals',
             'balanceOf', 'symbol', 'mint', 'transfer', 'free', 'allowance'})

    def test_initial_state(self):
        # Check total supply is 0
        self.assertEqual(self.c.totalSupply(), 0)

        # Check several account balances as 0
        self.assertEqual(self.c.balanceOf(self.t.a1), 0)
        self.assertEqual(self.c.balanceOf(self.t.a2), 0)
        self.assertEqual(self.c.balanceOf(self.t.a3), 0)

        # Check several allowances as 0
        self.assertEqual(self.c.allowance(self.t.a1, self.t.a1), 0)
        self.assertEqual(self.c.allowance(self.t.a1, self.t.a2), 0)
        self.assertEqual(self.c.allowance(self.t.a1, self.t.a3), 0)
        self.assertEqual(self.c.allowance(self.t.a2, self.t.a3), 0)

    def test_mint_and_free(self):

        #
        # Test scenario where a1 mints 2, frees twice
        # (check balance consistency)
        #

        # a1 mints 2
        self.assertEqual(self.c.balanceOf(self.t.a1), 0)
        self.assertIsNone(self.c.mint(2, sender=self.t.k1))
        self.assertEqual(self.c.balanceOf(self.t.a1), 2)
        self.assertEqual(self.c.totalSupply(), 2)

        # free 1
        self.assertTrue(self.c.free(1, sender=self.t.k1))
        self.assertEqual(self.c.balanceOf(self.t.a1), 1)
        self.assertEqual(self.c.totalSupply(), 1)

        # free 1
        self.assertTrue(self.c.free(1, sender=self.t.k1))
        self.assertEqual(self.c.balanceOf(self.t.a1), 0)
        self.assertEqual(self.c.totalSupply(), 0)

        # test free on empty balance
        self.assertFalse(self.c.free(1, sender=self.t.k1))
        self.assertEqual(self.c.balanceOf(self.t.a1), 0)
        self.assertEqual(self.c.totalSupply(), 0)

        #
        #  Test scenario where a2 mints 0, frees
        # (check balance consistency, false free)
        #
        self.assertIsNone(self.c.mint(0, sender=self.t.k2))
        self.assertEqual(self.c.balanceOf(self.t.a2), 0)
        self.assertEqual(self.c.totalSupply(), 0)
        self.assertFalse(self.c.free(1, sender=self.t.k2))
        self.assertEqual(self.c.balanceOf(self.t.a2), 0)
        self.assertEqual(self.c.totalSupply(), 0)

        # free 0 should be a NOP
        self.assertTrue(self.c.free(0, sender=self.t.k2))
        self.assertEqual(self.c.balanceOf(self.t.a2), 0)
        self.assertEqual(self.c.totalSupply(), 0)

    def test_totalSupply(self):
        #
        # Test total supply initially, after mint, between two free,
        # and after failed free
        #

        self.assertEqual(self.c.totalSupply(), 0)
        self.assertIsNone(self.c.mint(2, sender=self.t.k1))
        self.assertEqual(self.c.totalSupply(), 2)
        self.assertTrue(self.c.free(1, sender=self.t.k1))
        self.assertEqual(self.c.totalSupply(), 1)

        self.assertTrue(self.c.free(1, sender=self.t.k1))
        self.assertEqual(self.c.totalSupply(), 0)
        self.assertFalse(self.c.free(1, sender=self.t.k1))
        self.assertEqual(self.c.totalSupply(), 0)

        # Test that 0-valued mint can't affect supply
        self.assertIsNone(self.c.mint(value=0, sender=self.t.k1))
        self.assertEqual(self.c.totalSupply(), 0)

    def test_transfer(self):
        # Test interaction between mint/free and transfer
        self.assertFalse(self.c.free(1, sender=self.t.k2))
        self.assertIsNone(self.c.mint(2, sender=self.t.k1))
        self.assertTrue(self.c.free(1, sender=self.t.k1))
        self.assertTrue(self.c.transfer(self.t.a2, 1, sender=self.t.k1))
        self.assertFalse(self.c.free(1, sender=self.t.k1))
        self.assertTrue(self.c.free(1, sender=self.t.k2))
        self.assertFalse(self.c.free(1, sender=self.t.k2))
        # Ensure transfer fails with insufficient balance
        self.assertFalse(self.c.transfer(self.t.a1, 1, sender=self.t.k2))
        # Ensure 0-transfer always succeeds
        self.assertTrue(self.c.transfer(self.t.a1, 0, sender=self.t.k2))

    def test_transferFromAndAllowance(self):
        # Test interaction between mint/free and transferFrom
        self.assertFalse(self.c.free(1, sender=self.t.k2))
        self.assertIsNone(self.c.mint(1, sender=self.t.k1))
        self.assertIsNone(self.c.mint(1, sender=self.t.k2))
        self.assertTrue(self.c.free(1, sender=self.t.k1))
        # This should fail; no allowance or balance (0 always succeeds)
        self.assertFalse(self.c.transferFrom(self.t.a1, self.t.a3, 1, sender=self.t.k2))
        self.assertTrue(self.c.transferFrom(self.t.a1, self.t.a3, 0, sender=self.t.k2))
        # Correct call to approval should update allowance (but not for reverse pair)
        self.assertTrue(self.c.approve(self.t.a2, 1, sender=self.t.k1))
        self.assertEqual(self.c.allowance(self.t.a1, self.t.a2, sender=self.t.k3), 1)
        self.assertEqual(self.c.allowance(self.t.a2, self.t.a1, sender=self.t.k2), 0)
        # transferFrom should succeed when allowed, fail with wrong sender
        self.assertFalse(self.c.transferFrom(self.t.a2, self.t.a3, 1, sender=self.t.k3))
        self.assertEqual(self.c.balanceOf(self.t.a2), 1)
        self.assertTrue(self.c.approve(self.t.a1, 1, sender=self.t.k2))
        self.assertTrue(self.c.transferFrom(self.t.a2, self.t.a3, 1, sender=self.t.k1))
        # Allowance should be correctly updated after transferFrom
        self.assertEqual(self.c.allowance(self.t.a2, self.t.a1, sender=self.t.k2), 0)
        # transferFrom with no funds should fail despite approval
        self.assertTrue(self.c.approve(self.t.a1, 1, sender=self.t.k2))
        self.assertEqual(self.c.allowance(self.t.a2, self.t.a1, sender=self.t.k2), 1)
        self.assertFalse(self.c.transferFrom(self.t.a2, self.t.a3, 1, sender=self.t.k1))
        # 0-approve should not change balance or allow transferFrom to change balance
        self.assertIsNone(self.c.mint(1, sender=self.t.k2))
        self.assertEqual(self.c.allowance(self.t.a2, self.t.a1, sender=self.t.k2), 1)
        self.assertTrue(self.c.approve(self.t.a1, 0, sender=self.t.k2))
        self.assertEqual(self.c.allowance(self.t.a2, self.t.a1, sender=self.t.k2), 0)
        self.assertTrue(self.c.approve(self.t.a1, 0, sender=self.t.k2))
        self.assertEqual(self.c.allowance(self.t.a2, self.t.a1, sender=self.t.k2), 0)
        self.assertFalse(self.c.transferFrom(self.t.a2, self.t.a3, 1, sender=self.t.k1))
        # Test that if non-zero approval exists, 0-approval is required to proceed
        # as described in countermeasures at
        # https://docs.google.com/document/d/1YLPtQxZu1UAvO9cZ1O2RPXBbT0mooh4DYKjA_jp-RLM/edit#heading=h.m9fhqynw2xvt
        self.assertEqual(self.c.allowance(self.t.a2, self.t.a1, sender=self.t.k2), 0)
        self.assertTrue(self.c.approve(self.t.a1, 1, sender=self.t.k2))
        self.assertEqual(self.c.allowance(self.t.a2, self.t.a1, sender=self.t.k2), 1)
        self.assertFalse(self.c.approve(self.t.a1, 2, sender=self.t.k2))
        self.assertEqual(self.c.allowance(self.t.a2, self.t.a1, sender=self.t.k2), 1)
        # Check that approving 0 then amount works
        self.assertTrue(self.c.approve(self.t.a1, 0, sender=self.t.k2))
        self.assertEqual(self.c.allowance(self.t.a2, self.t.a1, sender=self.t.k2), 0)
        self.assertTrue(self.c.approve(self.t.a1, 5, sender=self.t.k2))
        self.assertEqual(self.c.allowance(self.t.a2, self.t.a1, sender=self.t.k2), 5)

    def test_payability(self):
        # Make sure functions are not payable

        # Non payable functions - ensure all fail with value, succeed without
        self.assert_tx_failed(lambda: self.c.mint(2, value=2, sender=self.t.k1))
        self.assertIsNone(self.c.mint(2, value=0, sender=self.t.k1))
        self.assert_tx_failed(lambda: self.c.free(0, value=2, sender=self.t.k1))
        self.assertTrue(self.c.free(0, value=0, sender=self.t.k1))
        self.assert_tx_failed(lambda: self.c.totalSupply(value=2, sender=self.t.k1))
        self.assertEqual(self.c.totalSupply(value=0, sender=self.t.k1), 2)
        self.assert_tx_failed(lambda: self.c.balanceOf(self.t.a1, value=2, sender=self.t.k1))
        self.assertEqual(self.c.balanceOf(self.t.a1, value=0, sender=self.t.k1), 2)
        self.assert_tx_failed(lambda: self.c.transfer(self.t.a2, 0, value=2, sender=self.t.k1))
        self.assertTrue(self.c.transfer(self.t.a2, 0, value=0, sender=self.t.k1))
        self.assert_tx_failed(lambda: self.c.approve(self.t.a2, 1, value=2, sender=self.t.k1))
        self.assertTrue(self.c.approve(self.t.a2, 1, value=0, sender=self.t.k1))
        self.assert_tx_failed(lambda: self.c.allowance(self.t.a1, self.t.a2, value=2, sender=self.t.k1))
        self.assertEqual(self.c.allowance(self.t.a1, self.t.a2, value=0, sender=self.t.k1), 1)
        self.assert_tx_failed(lambda: self.c.transferFrom(self.t.a1, self.t.a2, 0, value=2, sender=self.t.k1))
        self.assertTrue(self.c.transferFrom(self.t.a1, self.t.a2, 0, value=0, sender=self.t.k1))

    def test_raw_logs(self):
        self.s.head_state.receipts[-1].logs = []

        # Check that mint emits no event
        self.assertIsNone(self.c.mint(2, sender=self.t.k1))
        self.assertEqual(self.s.head_state.receipts[-1].logs, [])

        # Check that free emits not event
        self.assertTrue(self.c.free(1, sender=self.t.k1))
        self.assertEqual(self.s.head_state.receipts[-1].logs, [])

        # Check that transfer appropriately emits Transfer event
        self.assertTrue(self.c.transfer(self.t.a2, 1, sender=self.t.k1))
        self.check_logs([self.transfer_topic, bytes_to_int(self.t.a1),
                          bytes_to_int(self.t.a2)], (1).to_bytes(32, byteorder='big'))
        self.assertTrue(self.c.transfer(self.t.a2, 0, sender=self.t.k1))
        self.check_logs([self.transfer_topic, bytes_to_int(self.t.a1),
                          bytes_to_int(self.t.a2)], (0).to_bytes(32, byteorder='big'))

        # Check that approving amount emits events
        self.assertTrue(self.c.approve(self.t.a1, 1, sender=self.t.k2))
        self.check_logs([self.approval_topic, bytes_to_int(self.t.a2),
                          bytes_to_int(self.t.a1)], (1).to_bytes(32, byteorder='big'))
        self.assertTrue(self.c.approve(self.t.a2, 0, sender=self.t.k3))
        self.check_logs([self.approval_topic, bytes_to_int(self.t.a3),
                          bytes_to_int(self.t.a2)], (0).to_bytes(32, byteorder='big'))

        # Check that transferFrom appropriately emits Transfer event
        self.assertTrue(self.c.transferFrom(self.t.a2, self.t.a3, 1, sender=self.t.k1))
        self.check_logs([self.transfer_topic, bytes_to_int(self.t.a2),
                          bytes_to_int(self.t.a3)], (1).to_bytes(32, byteorder='big'))
        self.assertTrue(self.c.transferFrom(self.t.a2, self.t.a3, 0, sender=self.t.k1))
        self.check_logs([self.transfer_topic, bytes_to_int(self.t.a2),
                          bytes_to_int(self.t.a3)], (0).to_bytes(32, byteorder='big'))

        # Check that no other ERC-compliant calls emit any events
        self.s.head_state.receipts[-1].logs = []
        self.assertEqual(self.c.totalSupply(), 1)
        self.assertEqual(self.s.head_state.receipts[-1].logs, [])
        self.assertEqual(self.c.balanceOf(self.t.a1), 0)
        self.assertEqual(self.s.head_state.receipts[-1].logs, [])
        self.assertEqual(self.c.allowance(self.t.a1, self.t.a2), 0)
        self.assertEqual(self.s.head_state.receipts[-1].logs, [])

        # Check that failed approve, transfer calls emit no events
        self.assertFalse(self.c.transfer(self.t.a2, 1, sender=self.t.k1))
        self.assertEqual(self.s.head_state.receipts[-1].logs, [])
        self.assertFalse(self.c.transferFrom(self.t.a2, self.t.a3, 1, sender=self.t.k1))
        self.assertEqual(self.s.head_state.receipts[-1].logs, [])

        self.assertTrue(self.c.approve(self.t.a2, 2, sender=self.t.k3))
        self.check_logs([self.approval_topic, bytes_to_int(self.t.a3),
                          bytes_to_int(self.t.a2)], (2).to_bytes(32, byteorder='big'))
        self.s.head_state.receipts[-1].logs = []
        self.assertFalse(self.c.approve(self.t.a2, 3, sender=self.t.k3))
        self.assertEqual(self.s.head_state.receipts[-1].logs, [])

    def test_boundaries(self):
        MAX_UINT256 = (2 ** 256) - 1  # Max num256 value
        STORAGE_LOCATION_ARRAY = 0xFFFFFFFFFF  # beginning of storage in GST

        self.assert_tx_failed(lambda: self.c.mint(MAX_UINT256, sender=self.t.k1, startgas=10**8))
        self.assert_tx_failed(lambda: self.c.mint(MAX_UINT256 - STORAGE_LOCATION_ARRAY, sender=self.t.k1, startgas=10**8))
        self.assert_tx_failed(lambda: self.c.mint(MAX_UINT256 - STORAGE_LOCATION_ARRAY - 1, sender=self.t.k1, startgas=10**8))
        self.assertFalse(self.c.free(MAX_UINT256, sender=self.t.k1))
        self.assertFalse(self.c.free(MAX_UINT256 - STORAGE_LOCATION_ARRAY, sender=self.t.k1))
        self.assertFalse(self.c.free(MAX_UINT256 - STORAGE_LOCATION_ARRAY - 1, sender=self.t.k1))

        if self.c.freeUpTo is not None:
            self.assertFalse(self.c.freeUpTo(MAX_UINT256, sender=self.t.k1))
            self.assertFalse(self.c.freeUpTo(MAX_UINT256 - STORAGE_LOCATION_ARRAY, sender=self.t.k1))
            self.assertFalse(self.c.freeUpTo(MAX_UINT256 - STORAGE_LOCATION_ARRAY - 1, sender=self.t.k1))

        if self.c.freeFrom is not None:
            self.assertFalse(self.c.freeFrom(self.t.a0, MAX_UINT256, sender=self.t.k1))
            self.assertFalse(self.c.freeFrom(self.t.a0, MAX_UINT256 - STORAGE_LOCATION_ARRAY, sender=self.t.k1))
            self.assertFalse(self.c.freeFrom(self.t.a0, MAX_UINT256 - STORAGE_LOCATION_ARRAY - 1, sender=self.t.k1))

        if self.c.freeFromUpTo is not None:
            self.assertFalse(self.c.freeFromUpTo(self.t.a0, MAX_UINT256, sender=self.t.k1))
            self.assertFalse(self.c.freeFromUpTo(self.t.a0, MAX_UINT256 - STORAGE_LOCATION_ARRAY, sender=self.t.k1))
            self.assertFalse(self.c.freeFromUpTo(self.t.a0, MAX_UINT256 - STORAGE_LOCATION_ARRAY - 1, sender=self.t.k1))

    def test_internal_transfer_private(self):
        with self.assertRaises(AttributeError):
            self.c.internalTransfer(self.t.a0, self.t.a1, 0)
        fn_selector = utils.sha3("internalTransfer(address,address,uint256)")[:4]
        assert isinstance(fn_selector, bytes)
        data = fn_selector + self.t.a0 + self.t.a1 + 32 * b'\x00'
        with self.assertRaises(tester.TransactionFailed):
            self.s.tx(
                sender=self.t.k0,
                to=self.c.address,
                value=0,
                data=data,
                startgas=10**20)

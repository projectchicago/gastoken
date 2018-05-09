import unittest

from ethereum.tools import tester as t
from ethereum import utils as u
chain = t.Chain()

class TestBTCGasToken(unittest.TestCase)

    def setUp(self):
        pass

    def testBasicFunctionality(self):
        pass

    def test_ERC721_attributes(self):
        self.assertEqual(self.c.decimals(), 2)
        self.assertEqual(self.c.name(), b'BTCFees by gastoken.io')
        self.assertEqual(self.c.symbol(), b'BTCF')


if __name__ == '__main__':
    unittest.main(verbosity=2)


from matplotlib import pyplot as plt
import numpy as np
from matplotlib import rc
rc('font', **{'family': 'sans-serif', 'sans-serif': ['Helvetica']})
rc('text', usetex=True)

from .test_GST1 import TestGST1

STORAGE_TOKEN_COST = TestGST1.MINT_TOKEN_COST
STORAGE_FREE_COST = TestGST1.FREE_TOKEN_COST
STORAGE_REFUND = TestGST1.REFUND

from .test_GST2 import TestGST2
CONTRACT_TOKEN_COST = TestGST2.MINT_TOKEN_COST
CONTRACT_FREE_COST = TestGST2.FREE_TOKEN_COST
CONTRACT_REFUND = TestGST2.REFUND

gs = np.arange(1, 50, 1)

eff_storage = lambda g: STORAGE_REFUND * g / (STORAGE_TOKEN_COST + STORAGE_FREE_COST * g)
eff_contract = lambda g: CONTRACT_REFUND * g / (CONTRACT_TOKEN_COST + CONTRACT_FREE_COST * g)

plt.plot(gs, list(map(eff_storage, gs)),
         gs, list(map(eff_contract, gs)))

EXPECTED_BREAK_STORAGE = 2.01
EXPECTED_BREAK_CONTRACT = 2.13
EXPECTED_INTERSECTION = 3.71

break_storage = STORAGE_TOKEN_COST / (STORAGE_REFUND - STORAGE_FREE_COST)
break_contract = CONTRACT_TOKEN_COST / (CONTRACT_REFUND - CONTRACT_FREE_COST)

intersection = (STORAGE_TOKEN_COST * CONTRACT_REFUND - STORAGE_REFUND * CONTRACT_TOKEN_COST) \
               / (STORAGE_REFUND * CONTRACT_FREE_COST - CONTRACT_REFUND * STORAGE_FREE_COST)

assert np.round(break_storage, 2) == EXPECTED_BREAK_STORAGE, \
    "Expected {} got {}".format(EXPECTED_BREAK_STORAGE, np.round(break_storage, 2))
assert np.round(break_contract, 2) == EXPECTED_BREAK_CONTRACT, \
    "Expected {} got {}".format(EXPECTED_BREAK_CONTRACT, np.round(break_contract, 2))
assert np.round(intersection, 2) == EXPECTED_INTERSECTION, \
    "Expected {} got {}".format(EXPECTED_INTERSECTION, np.round(intersection, 2))

print("break even for storage: {:.2f}".format(break_storage))
print("break even for contract: {:.2f}".format(break_contract))
print('intersection at {:.2f}'.format(intersection))

plt.plot((EXPECTED_BREAK_STORAGE, EXPECTED_BREAK_STORAGE), (0, eff_storage(EXPECTED_BREAK_STORAGE)), 'k--')
plt.plot((0, EXPECTED_BREAK_STORAGE), (eff_storage(EXPECTED_BREAK_STORAGE), eff_storage(EXPECTED_BREAK_STORAGE)), 'k--')

plt.plot((EXPECTED_INTERSECTION, EXPECTED_INTERSECTION), (0, eff_storage(EXPECTED_INTERSECTION)), 'k--')
plt.plot((0, EXPECTED_INTERSECTION), (eff_storage(EXPECTED_INTERSECTION), eff_storage(EXPECTED_INTERSECTION)), 'k--')


plt.xlim([0, gs[-1]])
plt.ylim([0, 1.1 * eff_contract(gs[-1])])

plt.legend(['GST1 (storage based)', 'GST2 (contract based)'])
plt.xlabel(r'$gas_{high} / gas_{low}$')
plt.ylabel('Maximal Savings/Efficiency')
plt.savefig('comp.png')

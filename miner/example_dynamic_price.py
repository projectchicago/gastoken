from __future__ import print_function

from eth_abi import encode_abi
from eth_utils import (
    encode_hex,
    function_abi_to_4byte_selector,
)
import web3, time, json
from ethereum.tester import languages

batch_size = 4
w3 = web3.Web3(web3.IPCProvider('/home/debian/geth_temp_fast/geth.ipc'))
timeout = 999999999 # seconds
batch_timeout = 1000
wei_per_second = 42738118437506803190 / (604800.0 * 2.8) # target wei to consume / (seconds in 1wk)
code = '/home/ubuntu/gas/token.sol'
pool_addr = '0xTODO' # your address here
contract_address = "0x0000000000b3f879cb30fe243b4dfee438691c04"
gas_price = int(4e9) + 5 # start gas price (1gwei + epsilon)
gas_delta = int(2e9)
max_buy = int(25e9)
abi = json.loads('[{"constant":false,"inputs":[{"name":"spender","type":"address"},{"name":"value","type":"uint256"}],"name":"approve","outputs":[{"name":"success","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"name":"totalSupply","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"from","type":"address"},{"name":"to","type":"address"},{"name":"value","type":"uint256"}],"name":"transferFrom","outputs":[{"name":"success","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"name":"owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"value","type":"uint256"}],"name":"mint","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"to","type":"address"},{"name":"value","type":"uint256"}],"name":"transfer","outputs":[{"name":"success","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"value","type":"uint256"}],"name":"free","outputs":[{"name":"success","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"name":"owner","type":"address"},{"name":"spender","type":"address"}],"name":"allowance","outputs":[{"name":"remaining","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"anonymous":false,"inputs":[{"indexed":true,"name":"from","type":"address"},{"indexed":true,"name":"to","type":"address"},{"indexed":false,"name":"value","type":"uint256"}],"name":"Transfer","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"owner","type":"address"},{"indexed":true,"name":"spender","type":"address"},{"indexed":false,"name":"value","type":"uint256"}],"name":"Approval","type":"event"}]')
tx_gas_consumed = 982614

# Load old batch times
# batchtimes is list of (end_nonce,time_start,time_end,wei_consumed)
batchtimes = open("batchtimes").read().splitlines()
batchtimes = [[int(float(y)) for y in x.split(",")] for x in batchtimes]

print("Initial batchtimes loaded, showing last 50")
print(batchtimes[-50:])

while True:
    batch_start_nonce = w3.eth.getTransactionCount(pool_addr)
    curr_nonce = batch_start_nonce
    while True:
        try:
            w3.personal.unlockAccount(pool_addr, '')
            break
        except:
            pass
    t0 = time.time()
    # do tx
    fn_abi = abi[4]
    assert fn_abi['name'] == 'mint'
    fn_selector = function_abi_to_4byte_selector(fn_abi)
    if gas_price > max_buy:
        gas_price = max_buy
    assert(gas_price <= max_buy) # sanity check circuit breaker
    for i in range(0, batch_size):
        transaction = {
            "from": pool_addr,
            "to": contract_address,
            "gas": 999999, # 982615, 0x1a | 216k 5
            "gasPrice": (gas_price),
            "data": encode_hex(fn_selector + encode_abi(["uint256"], [0x1a])),
            "nonce": curr_nonce
        }
        txn_hash = None
        while True:
            try:
                txn_hash = w3.eth.sendTransaction(transaction)
                break
            except Exception as e:
                print("web3 comms failed")
                print(e)
                if "known" in str(e) or "underpriced" in str(e):
                    break # script was restarted, tx already sent
                time.sleep(5)
        print("tx sent", txn_hash, curr_nonce)
        curr_nonce += 1
    batch_sent = time.time()
    print("batch sent!", batch_sent)
    while True:
        try:
            timed_out = False
            while w3.eth.getTransactionCount(pool_addr) < (batch_start_nonce + batch_size):
                time.sleep(2)
                if time.time() - batch_sent > batch_timeout:
                    gas_price += gas_delta
                    timed_out = True
                    print("Timed out, upping price.  New price", gas_price)
                    break
            if timed_out:
                break
            curr_nonce = w3.eth.getTransactionCount(pool_addr)
            # batchtimes is list of (end_nonce,time_start,time_end,wei_consumed)
            batchtuple = (curr_nonce,batch_sent,time.time(),1.0*gas_price*tx_gas_consumed*batch_size)
            batchtimes += [batchtuple]
            print("batch mined", batchtuple)
            open("batchtimes", "a").write(",".join([str(int(x)) for x in batchtuple]) + "\n")
            burn_rate = batchtuple[3] / (batchtuple[2] - batchtuple[1])
            adjustment_factor = min(max((wei_per_second / burn_rate), .75), 2.0)
            new_price = max(int(adjustment_factor * gas_price), int(1e9) + 20)
            print("Adjusting gas.  Burn rate / target / adjustment factor / old gas / new gas")
            print(burn_rate, wei_per_second, adjustment_factor, gas_price, new_price)
            gas_price = new_price
            break
        except Exception as e:
            print(e)
            pass




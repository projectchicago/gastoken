from eth_abi import encode_abi
from eth_utils import (
    encode_hex,
    function_abi_to_4byte_selector,
)
import web3, time, json
from ethereum.tester import languages

BATCH_SIZE = 4
w3 = web3.Web3(web3.IPCProvider('/home/debian/geth_temp_fast/geth.ipc'))
timeout = 999999999 # seconds
batch_timeout = 1200
gas_delta = 0
pool_addr = '0xTODO' # your addr here
contract_address = "0x0000000000b3f879cb30fe243b4dfee438691c04"
gas_price = int(6e9) + 5 # desired gas price here TODO
abi = json.loads('[{"constant":false,"inputs":[{"name":"spender","type":"address"},{"name":"value","type":"uint256"}],"name":"approve","outputs":[{"name":"success","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"name":"totalSupply","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"from","type":"address"},{"name":"to","type":"address"},{"name":"value","type":"uint256"}],"name":"transferFrom","outputs":[{"name":"success","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"name":"owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"value","type":"uint256"}],"name":"mint","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"to","type":"address"},{"name":"value","type":"uint256"}],"name":"transfer","outputs":[{"name":"success","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"value","type":"uint256"}],"name":"free","outputs":[{"name":"success","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"name":"owner","type":"address"},{"name":"spender","type":"address"}],"name":"allowance","outputs":[{"name":"remaining","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"anonymous":false,"inputs":[{"indexed":true,"name":"from","type":"address"},{"indexed":true,"name":"to","type":"address"},{"indexed":false,"name":"value","type":"uint256"}],"name":"Transfer","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"owner","type":"address"},{"indexed":true,"name":"spender","type":"address"},{"indexed":false,"name":"value","type":"uint256"}],"name":"Approval","type":"event"}]')
start_nonce = w3.eth.getTransactionCount(pool_addr)

curr_nonce = start_nonce
while True:
    batch_start_nonce = w3.eth.getTransactionCount(pool_addr)
    w3.personal.unlockAccount(pool_addr, '')
    t0 = time.time()
    # do tx
    fn_abi = abi[4]
    assert fn_abi['name'] == 'mint'
    fn_selector = function_abi_to_4byte_selector(fn_abi)
    for i in range(0, BATCH_SIZE):
        transaction = {
        "from": pool_addr,
        "to": contract_address,
        "gas": 999000 + gas_delta, # 1M, 0x1a | 216k 5
        "gasPrice": (gas_price),
        "data": encode_hex(fn_selector + encode_abi(["uint256"], [0x1a])),
        }
        if curr_nonce is not None:
            transaction["nonce"] = curr_nonce
            curr_nonce += 1
        txn_hash = w3.eth.sendTransaction(transaction)
        print(txn_hash, curr_nonce - 1)
        receipt = None
    batch_done = time.time()
    while True:
        try:
            while w3.eth.getTransactionCount(pool_addr) < batch_start_nonce + BATCH_SIZE and time.time() - batch_done < batch_timeout:
                time.sleep(2)
            curr_nonce = w3.eth.getTransactionCount(pool_addr)
            if time.time() - batch_done > batch_timeout:
                gas_delta += 1
            break
        except:
            pass
    print(time.time(), "\n", receipt)



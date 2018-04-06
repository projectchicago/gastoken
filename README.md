# GasToken (<https://gastoken.io>)

GasToken is an Ethereum ERC20 smart contract that lets users tokenize gas, an internal resource used in Ethereum to pay for transactions.
The idea is simple: store gas when gas prices are low, release it when gas prices are high and experience lower transaction fees. GasTokens can be traded like any other ERC20 token.

The details on how GasToken works can be found here: <https://gastoken.io>

This repository contains the Solidity code for two GasToken variants (GST1 and GST2) and exhaustive test suites of those contracts' functionalities. The `contract/` folder contains our smart contracts, the `test/` folder contains our pyethereum.tester based test suite.

## Deployments

The contracts are deployed on Ethereum, Kovan (testnet), Rinkeby (testnet), Ropsten Revived (testnet), and Ethereum Classic.

**Ethereum**
+ GST1: [`0x88d60255F917e3eb94eaE199d827DAd837fac4cB`](https://etherscan.io/address/0x88d60255f917e3eb94eae199d827dad837fac4cb)
+ GST2: [`0x0000000000b3F879cb30FE243b4Dfee438691c04`](https://etherscan.io/address/0x0000000000b3f879cb30fe243b4dfee438691c04)

**Ropsten**
+ GST1: [`0x88d60255F917e3eb94eaE199d827DAd837fac4cB`](https://ropsten.etherscan.io/address/0x88d60255f917e3eb94eae199d827dad837fac4cb)
+ GST2: [`0x0000000000b3F879cb30FE243b4Dfee438691c04`](https://ropsten.etherscan.io/address/0x0000000000b3f879cb30fe243b4dfee438691c04)

**Rinkeby**
+ GST1: [`0x88d60255F917e3eb94eaE199d827DAd837fac4cB`](https://rinkeby.etherscan.io/address/0x88d60255f917e3eb94eae199d827dad837fac4cb)
+ GST2: [`0x0000000000b3F879cb30FE243b4Dfee438691c04`](https://rinkeby.etherscan.io/address/0x0000000000b3f879cb30fe243b4dfee438691c04)

**Kovan**
+ GST1: [`0x88d60255F917e3eb94eaE199d827DAd837fac4cB`](https://kovan.etherscan.io/address/0x88d60255f917e3eb94eae199d827dad837fac4cb)
+ GST2: [`0x0000000000170CcC93903185bE5A2094C870Df62`](https://kovan.etherscan.io/address/0x0000000000170ccc93903185be5a2094c870df62)

**Ethereum Classic**
+ GST1: [`0x88d60255F917e3eb94eaE199d827DAd837fac4cB`](http://gastracker.io/contract/0x88d60255F917e3eb94eaE199d827DAd837fac4cB)
+ GST2: [`0x0000000000b3F879cb30FE243b4Dfee438691c04`](http://gastracker.io/contract/0x0000000000b3F879cb30FE243b4Dfee438691c04)

The GST2 code deployed on Ethereum Classic slightly differs from that on Ethereum and the testnets. For details, check out `contract/GST2_ETC.sol`

## Dependencies

The code was tested using python 3.6.2 and Solidity Version: 0.4.18+commit.9cf6e910.Darwin.appleclang

Run

```sh
$ python -m pip install -r requirements.txt
```
to install the required dependencies.

## Run Tests

To run the tests for the Storage-based GasToken (GST1), run

```sh
$ python -m test.test_GST1
```

To run the tests for the Contract-based GasToken (GST2), run

```sh
$ python -m test.test_GST2
```

To run tests for the RLP encoding used in GST2, run

```sh
$ python -m test.test_rlp
```

## Authors

We are a team of blockchain researchers from around the world:

<ul>
<li><a href="https://twitter.com/ethlorenz">Lorenz Breidenbach</a> (<a href="https://www.ethz.ch">ETH Zürich</a>, <a href="https://tech.cornell.edu/">Cornell Tech</a>, <a href="http://www.initc3.org/">IC3</a>)</li>
<li><a href="http://pdaian.com">Phil Daian</a> (<a href="https://tech.cornell.edu/">Cornell Tech</a>, <a href="http://www.initc3.org/">IC3</a>)</li>
<li><a href="http://floriantramer.com/">Florian Tramèr</a> (<a href="https://www.stanford.edu/">Stanford University</a>)</li>
</ul>

with advice, review, and support from <a href="http://www.arijuels.com/">Ari Juels</a> (<a  href="https://tech.cornell.edu/">Cornell Tech</a>, <a href="http://www.initc3.org/">IC3</a>, <a href="https://tech.cornell.edu/jacobs-technion-cornell-institute/overview">The Jacobs Institute</a>).

We offer absolutely no support, guarantees, advice, or other help with GasToken. If you like it, use it.

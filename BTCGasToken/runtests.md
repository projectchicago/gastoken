# How to Run the Unit Tests

Start a truffle develop, make sure your truffle.js points development at the truffle develop endpoint (localhost port 9545). Then:

```bash 
truffle test test/BTCGasTokenNonRinkeby.js --network development
```


For the Town Crier required tests, you will have to test on rinkeby. Set up your geth/parity endpoint in [truffle.js](http://truffleframework.com/docs/advanced/networks), then you can test the rinkeby tests (warning, will run very slow) like so:

```bash 
truffle test test/BTCGasToken.js --network rinkeby
```

See the truffle.js in this repo for reference.


To run coverage, install [solidity-coverage](https://github.com/sc-forks/solidity-coverage) and run it like so: `./node_modules/.bin/solidity-coverage`

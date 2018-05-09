require('truffle-test-utils').init();

var BTCGasTokenArtifact = artifacts.require("BTCGasToken");
var MockTownCrierArtifact = artifacts.require("MockTownCrier");

contract('BTCGasToken', function(accounts) {

  it("should have a name and ticker that are proper", async () => {
    let instance = await BTCGasTokenArtifact.deployed();
    let retName = await instance.name();
    assert.equal(retName, "BTCFees by gastoken.io", "Name on contract does not match expected value");
    let retSymbol = await instance.symbol();
    assert.equal(retSymbol, "BTCF", "Symbol on contract does not match expected value");
  });

  it("should properly mint a token and fire an event", async () => {
    let instance = await BTCGasTokenArtifact.deployed();
    let mintedTransaction = await instance.mint(new web3.BigNumber("20000000000000000"),  new web3.BigNumber("50000"), new web3.BigNumber("2254128"), { "from": accounts[1],"value": ( new web3.BigNumber("10000000000000000" ) ) } ) ;
    let supply = await instance.totalSupply();
    assert.equal(supply.toString(), "1", "Minting should increase supply...");
    assert.web3Event(mintedTransaction, {
      'event': 'DerivativeCreated',
      'args': {
        'id': 0,
        'maker': accounts[1],
        'makerAmount': 10000000000000000,
        'takerAmount' : 20000000000000000,
        'triggerPrice': 50000,
        'triggerHeight': 2254128,
      }
    });
  });

  it("should properly allow someone to take tokens", async () => {
    let instance = await BTCGasTokenArtifact.deployed();
    let bn = web3.eth.blockNumber;
    let mintedTransaction = await instance.mint(new web3.BigNumber("20000000000000000"),  new web3.BigNumber("50000"), new web3.BigNumber(bn+1000), { "from": accounts[1],"value": ( new web3.BigNumber("10000000000000000" ) ) } ) ;
    assert.web3Event(mintedTransaction, {
      'event': 'DerivativeCreated',
      'args': {
        'id': 1,
        'maker': accounts[1],
        'makerAmount': 10000000000000000,
        'takerAmount' : 20000000000000000,
        'triggerPrice': 50000,
        'triggerHeight': bn+1000,
      }
    });
    
    let takenTransaction = await instance.take(new web3.BigNumber("1"), { "from": accounts[2], "value": new web3.BigNumber("20000000000000000") } );
    assert.web3Event(takenTransaction, {
      'event': 'DerivativeTaken',
      'args': {
        'id': 1,
        'maker': accounts[1],
        'taker': accounts[2],
        'makerAmount': 10000000000000000,
        'takerAmount' : 20000000000000000,
        'triggerPrice': 50000,
        'triggerHeight': bn+1000,
      }
    });
  });

  it("should let someone cancel their own token mint", async () => {
    let instance = await BTCGasTokenArtifact.deployed();
    let bn = web3.eth.blockNumber;
    let mintedTransaction = await instance.mint(new web3.BigNumber("20000000000000000"),  new web3.BigNumber("50000"), new web3.BigNumber(bn+10), { "from": accounts[1],"value": ( new web3.BigNumber("10000000000000000" ) ) } );
    assert.web3Event(mintedTransaction, {
      'event': 'DerivativeCreated',
      'args': {
        'id': 2,
        'maker': accounts[1],
        'makerAmount': 10000000000000000,
        'takerAmount' : 20000000000000000,
        'triggerPrice': 50000,
        'triggerHeight': bn+10,
      }
    });
    let canceledTransaction = await instance.cancel(new web3.BigNumber("2"), {"from":accounts[1], "value": 0} );
    assert.web3Event(canceledTransaction, {
      'event': 'DerivativeCanceled',
      'args': {
        'id': 2,
        'maker': accounts[1],
        'makerAmount': 10000000000000000,
        'takerAmount' : 20000000000000000,
        'triggerPrice': 50000,
        'triggerHeight': bn+10,
      }
    });
  });

});


require('truffle-test-utils').init();

var BTCGasTokenArtifact = artifacts.require("BTCGasToken");
var MockTownCrierArtifact = artifacts.require("MockTownCrier");

contract('BTCGasToken', function(accounts) {

it("should not let someone cancel token mints that they do not own", async () => {
    let instance = await BTCGasTokenArtifact.deployed();
    let bn = web3.eth.blockNumber;
    let mintedTransaction = await instance.mint(new web3.BigNumber("20000000000000000"),  new web3.BigNumber("50000"), new web3.BigNumber(bn+10), { "from": accounts[1],"value": ( new web3.BigNumber("10000000000000000" ) ) } );
    assert.web3Event(mintedTransaction, {
      'event': 'DerivativeCreated',
      'args': {
        'id': 0,
        'maker': accounts[1],
        'makerAmount': 10000000000000000,
        'takerAmount' : 20000000000000000,
        'triggerPrice': 50000,
        'triggerHeight': bn+10,
      }
    });
    try {
      let canceledTransaction = await instance.cancel(new web3.BigNumber("0"), {"from":accounts[2], "value": 0} );
      assert.fail("Canceled transaction from a different account should revert");
    } catch(error) {
      let revert = error.message.search('revert') >= 0;
      assert.isTrue(revert, "The EVM should revert since the require statement should fail");
    }
  });

  it("should not let someone cancel a taken derivative", async () => {
    let instance = await BTCGasTokenArtifact.deployed();
    let takenTransaction = await instance.take(new web3.BigNumber("0"), { "from": accounts[2], "value": new web3.BigNumber("20000000000000000") } );
    try {
      let canceledTransaction = await instance.cancel(new web3.BigNumber("0"), { "from": accounts[1], "value": 0 } );
      assert.fail("cancel transaction should revert.");
    } catch(error) {
      let revert = error.message.search('revert') >= 0;
      assert.isTrue(revert, "The EVM should revert since the require statement should fail");
    }
  });

  it("should not let someone cancel a non-existent derivative", async () => {
    let instance = await BTCGasTokenArtifact.deployed();
    try {
      let canceledTransaction = await instance.cancel(new web3.BigNumber("5000000"), { "from": accounts[2], "value": 0 } );
      assert.fail("cancel transaction should revert.");
    } catch(error) {
      let revert = error.message.search('revert') >= 0;
      assert.isTrue(revert, "The EVM should revert since the require statement should fail");
    }
  });

 it("should not let someone mint without putting up the minimum amount of money", async () => {
    let instance = await BTCGasTokenArtifact.deployed();
    let bn = web3.eth.blockNumber;
    try {
      let mintedTransaction = await instance.mint(new web3.BigNumber("20000000000000000"),  new web3.BigNumber("50000"), new web3.BigNumber(bn+10), { "from": accounts[1],"value": ( new web3.BigNumber("3000" ) ) } );
      assert.fail("Mint transaction should revert.");
    } catch(error) {
      let revert = error.message.search('revert') >= 0;
      assert.isTrue(revert, "The EVM should revert since the require statement should fail");
    }
  });

  it("should not let someone mint with a trigger height in the past", async () => {
    let instance = await BTCGasTokenArtifact.deployed();
    let bn = web3.eth.blockNumber;
    try {
      let mintedTransaction = await instance.mint(new web3.BigNumber("20000000000000000"),  new web3.BigNumber("50000"), new web3.BigNumber(bn-10), { "from": accounts[1],"value": ( new web3.BigNumber("20000000000000000" ) ) } );
      assert.fail("Mint transaction should revert.");
    } catch(error) {
      let revert = error.message.search('revert') >= 0;
      assert.isTrue(revert, "The EVM should revert since the require statement should fail");
    }
  });

it("should not let someone mint without forcing the taker amount to be greater than the town crier fee", async () => {
    // town crier fee right now is 7500000000000000 wei
    let townCrierFee = new web3.BigNumber("7400000000000000");
    let instance = await BTCGasTokenArtifact.deployed();
    let bn = web3.eth.blockNumber;
    try {
      let mintedTransaction = await instance.mint(townCrierFee,  new web3.BigNumber("50000"), new web3.BigNumber(bn+10), { "from": accounts[1],"value": ( new web3.BigNumber("10000000000000000" ) ) } );
      assert.fail("Mint transaction should revert.");
    } catch(error) {
      let revert = error.message.search('revert') >= 0;
      assert.isTrue(revert, "The EVM should revert since the require statement should fail");
    }
  });

  it("should not let someone take a non-existent derivative", async () => {
    let instance = await BTCGasTokenArtifact.deployed();
    try {
      let takenTransaction = await instance.take(new web3.BigNumber("5000000"), { "from": accounts[2], "value": 0 } );
      assert.fail("take transaction should revert.");
    } catch(error) {
      let revert = error.message.search('revert') >= 0;
      assert.isTrue(revert, "The EVM should revert since the require statement should fail");
    }
  });

  it("should not let someone take a derivative where the block number is greater than the trigger height", async () => {
    let instance = await BTCGasTokenArtifact.deployed();
    let bn = web3.eth.blockNumber;
    let mintedTransaction = await instance.mint(new web3.BigNumber("20000000000000000"),  new web3.BigNumber("50000"), new web3.BigNumber(bn+2), { "from": accounts[1],"value": ( new web3.BigNumber("10000000000000000" ) ) } ) ;
    assert.web3Event(mintedTransaction, {
      'event': 'DerivativeCreated',
      'args': {
        'id': 1,
        'maker': accounts[1],
        'makerAmount': 10000000000000000,
        'takerAmount' : 20000000000000000,
        'triggerPrice': 50000,
        'triggerHeight': bn+2,
      }
    });

    web3.currentProvider.sendAsync({
          jsonrpc: "2.0",
          method: "evm_mine",
          id: 12345
    }, function(){} );

    web3.currentProvider.sendAsync({
          jsonrpc: "2.0",
          method: "evm_mine",
          id: 12345
    }, function(){} );

    try {
      let takenTransaction = await instance.take(new web3.BigNumber("1"), { "from": accounts[2], "value": new web3.BigNumber("20000000000000000") } );
      assert.fail("take transaction should revert.");
    } catch(error) {
      let revert = error.message.search('revert') >= 0;
      assert.isTrue(revert, "The EVM should revert since the require statement should fail");
    }
  });

  it("should not let someone take a derivative that has already been taken", async () => {
    let instance = await BTCGasTokenArtifact.deployed();
    let bn = web3.eth.blockNumber;
    let mintedTransaction = await instance.mint(new web3.BigNumber("20000000000000000"),  new web3.BigNumber("50000"), new web3.BigNumber(bn+5), { "from": accounts[1],"value": ( new web3.BigNumber("10000000000000000" ) ) } ) ;
    let takenTransaction = await instance.take(new web3.BigNumber("2"), { "from": accounts[2], "value": new web3.BigNumber("20000000000000000") } );
    try {
      let takenTransaction = await instance.take(new web3.BigNumber("2"), { "from": accounts[2], "value": new web3.BigNumber("20000000000000000") } );
      assert.fail("take transaction should revert.");
    } catch(error) {
      let revert = error.message.search('revert') >= 0;
      assert.isTrue(revert, "The EVM should revert since the require statement should fail");
    }
  });

  it("should not let someone take a derivative when they havent sent enough money to match the taker amount", async () => {
    let instance = await BTCGasTokenArtifact.deployed();
    let bn = web3.eth.blockNumber;
    let mintedTransaction = await instance.mint(new web3.BigNumber("20000000000000000"),  new web3.BigNumber("50000"), new web3.BigNumber(bn+10), { "from": accounts[1],"value": ( new web3.BigNumber("10000000000000000" ) ) } ) ;
    assert.web3Event(mintedTransaction, {
      'event': 'DerivativeCreated',
      'args': {
        'id': 3,
        'maker': accounts[1],
        'makerAmount': 10000000000000000,
        'takerAmount' : 20000000000000000,
        'triggerPrice': 50000,
        'triggerHeight': bn+10,
      }
    });

    try {
      let takenTransaction = await instance.take(new web3.BigNumber("3"), { "from": accounts[2], "value": new web3.BigNumber("10") } );
      assert.fail("take transaction should revert.");
    } catch(error) {
      let revert = error.message.search('revert') >= 0;
      assert.isTrue(revert, "The EVM should revert since the require statement should fail");
    }
  });

// actually this fails on the require(!d.taken) statement, but that's fine. To be settled you must always first be taken anyways
it("should not let someone take a derivative that has already been settled", async () => {
    let instance = await BTCGasTokenArtifact.deployed();
    let bn = web3.eth.blockNumber;
    let mintedTransaction = await instance.mint(new web3.BigNumber("20000000000000000"),  new web3.BigNumber("50000"), new web3.BigNumber(bn+3), { "from": accounts[1],"value": ( new web3.BigNumber("10000000000000000" ) ) } ) ;
    let takenTransaction = await instance.take(new web3.BigNumber("4"), { "from": accounts[2], "value": new web3.BigNumber("20000000000000000") } );

    web3.currentProvider.sendAsync({
          jsonrpc: "2.0",
          method: "evm_mine",
          id: 12346
    }, function(){} );
    web3.currentProvider.sendAsync({
          jsonrpc: "2.0",
          method: "evm_mine",
          id: 12347
    }, function(){} );

    let settleTransaction = await instance.settle(new web3.BigNumber("4"), { "from": accounts[4] } );

    try {
      let takenTransaction = await instance.take(new web3.BigNumber("4"), { "from": accounts[3], "value": new web3.BigNumber("20000000000000000") } );
      assert.fail("take transaction should revert.");
    } catch(error) {
      let revert = error.message.search('revert') >= 0;
      assert.isTrue(revert, "The EVM should revert since the require statement should fail");
    }
  });

  it("should not let you settle a derivative that does not exist", async () => {
    let instance = await BTCGasTokenArtifact.deployed();
    let bn = web3.eth.blockNumber;

    try {
      let settleTransaction = await instance.settle(new web3.BigNumber("303423"), { "from": accounts[4] } );
      assert.fail("settle transaction should revert.");
    } catch(error) {
      let revert = error.message.search('revert') >= 0;
      assert.isTrue(revert, "The EVM should revert since the require statement should fail");
    }
  });

  it("should not let you settle a derivative prior to the trigger height being realized", async () => {
    let instance = await BTCGasTokenArtifact.deployed();
    let bn = web3.eth.blockNumber;
    let mintedTransaction = await instance.mint(new web3.BigNumber("20000000000000000"),  new web3.BigNumber("50000"), new web3.BigNumber("5000"), { "from": accounts[1],"value": ( new web3.BigNumber("10000000000000000" ) ) } ) ;
    let takenTransaction = await instance.take(new web3.BigNumber("5"), { "from": accounts[2], "value": new web3.BigNumber("20000000000000000") } );

    try {
      let settleTransaction = await instance.settle(new web3.BigNumber("5"), { "from": accounts[4] } );
      assert.fail("settle transaction should revert.");
    } catch(error) {
      let revert = error.message.search('revert') >= 0;
      assert.isTrue(revert, "The EVM should revert since the require statement should fail");
    }
  });

  it("should not let you settle a derivative that hasn't yet been taken", async () => {
    let instance = await BTCGasTokenArtifact.deployed();
    let bn = web3.eth.blockNumber;
    let mintedTransaction = await instance.mint(new web3.BigNumber("20000000000000000"),  new web3.BigNumber("50000"), new web3.BigNumber(bn+2), { "from": accounts[1],"value": ( new web3.BigNumber("10000000000000000" ) ) } ) ;

    web3.currentProvider.sendAsync({
          jsonrpc: "2.0",
          method: "evm_mine",
          id: 12346
    }, function(){} );
    web3.currentProvider.sendAsync({
          jsonrpc: "2.0",
          method: "evm_mine",
          id: 12347
    }, function(){} );
    web3.currentProvider.sendAsync({
          jsonrpc: "2.0",
          method: "evm_mine",
          id: 12347
    }, function(){} );

    try {
      let settleTransaction = await instance.settle(new web3.BigNumber("6"), { "from": accounts[4] } );
      assert.fail("settle transaction should revert.");
    } catch(error) {
      let revert = error.message.search('revert') >= 0;
      assert.isTrue(revert, "The EVM should revert since the require statement should fail");
    }
  });

  it("should not let you settle a derivative that has already been settled", async () => {
    let instance = await BTCGasTokenArtifact.deployed();
    let bn = web3.eth.blockNumber;
    let mintedTransaction = await instance.mint(new web3.BigNumber("20000000000000000"),  new web3.BigNumber("50000"), new web3.BigNumber(bn+3), { "from": accounts[1],"value": ( new web3.BigNumber("10000000000000000" ) ) } ) ;
    let takenTransaction = await instance.take(new web3.BigNumber("7"), { "from": accounts[2], "value": new web3.BigNumber("20000000000000000") } );

    web3.currentProvider.sendAsync({
          jsonrpc: "2.0",
          method: "evm_mine",
          id: 12347
    }, function(){} );

    let settleTransaction = await instance.settle(new web3.BigNumber("7"), { "from": accounts[4] } );

    try {
      let settleTransaction = await instance.settle(new web3.BigNumber("7"), { "from": accounts[4] } );
      assert.fail("settle transaction should revert.");
    } catch(error) {
      let revert = error.message.search('revert') >= 0;
      assert.isTrue(revert, "The EVM should revert since the require statement should fail");
    }
  });

  it("Nobody but town crier should be able to call the town crier callback function", async () => {
    let instance = await BTCGasTokenArtifact.deployed();
    let bn = web3.eth.blockNumber;

    try {
      let handlerCall = await instance.tcBTCFeeHandler(new web3.BigNumber("2"), new web3.BigNumber("0"), new web3.BigNumber("4"), { "from": accounts[0] } );
      assert.fail("transaction should revert.");
    } catch(error) {
      let revert = error.message.search('revert') >= 0;
      assert.isTrue(revert, "The EVM should revert since the require statement should fail");
    }
  });


});


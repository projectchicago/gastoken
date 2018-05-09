require('truffle-test-utils').init();

var BTCGasTokenArtifact = artifacts.require("BTCGasToken");
var MockTownCrierArtifact = artifacts.require("MockTownCrier");

contract('BTCGasToken', function(accounts) {

  it("should properly allow someone to mint, take, and settle tokens (Maker Wins)", async () => {
    let instance = await BTCGasTokenArtifact.deployed();
    let mocker = await MockTownCrierArtifact.deployed();
    let bn = web3.eth.blockNumber;
    var gasCost;

    let startingTakerAccountValue = web3.eth.getBalance(accounts[2]);
    let startingMakerAccountValue = web3.eth.getBalance(accounts[1]);

    let mintedTransaction = await instance.mint(new web3.BigNumber("20000000000000000"),  new web3.BigNumber("50000"), new web3.BigNumber(bn+3), { "from": accounts[1],"value": ( new web3.BigNumber("10000000000000000" ) ) } ) ;
    assert.web3Event(mintedTransaction, {
      'event': 'DerivativeCreated',
      'args': {
        'id': 0,
        'maker': accounts[1],
        'makerAmount': 10000000000000000,
        'takerAmount' : 20000000000000000,
        'triggerPrice': 50000,
        'triggerHeight': bn+3,
      }
    });
    
    let mintTx = await web3.eth.getTransaction(mintedTransaction.tx);
    gasCost = mintTx.gasPrice.mul(mintedTransaction.receipt.gasUsed);
    let afterMakeMakerValue = web3.eth.getBalance(accounts[1]);
    assert.equal(
        afterMakeMakerValue.toNumber(),
        ((startingMakerAccountValue.minus(gasCost).minus((new web3.BigNumber("10000000000000000")))).toNumber()),
        "Minting costs money, numbers don't match up."
    );


    let takenTransaction = await instance.take(new web3.BigNumber("0"), { "from": accounts[2], "value": new web3.BigNumber("20000000000000000") } );
    assert.web3Event(takenTransaction, {
      'event': 'DerivativeTaken',
      'args': {
        'id': 0,
        'maker': accounts[1],
        'taker': accounts[2],
        'makerAmount': 10000000000000000,
        'takerAmount' : 20000000000000000,
        'triggerPrice': 50000,
        'triggerHeight': bn+3,
      }
    });

    let takenTx = await web3.eth.getTransaction(takenTransaction.tx);
    gasCost = takenTx.gasPrice.mul(takenTransaction.receipt.gasUsed);
    let afterTakeTakerValue = web3.eth.getBalance(accounts[2]);
    assert.equal(
        afterTakeTakerValue.toNumber(),
        ((startingTakerAccountValue.minus(gasCost).minus((new web3.BigNumber("20000000000000000")))).toNumber()),
        "Taking costs money, numbers don't match up."
    );


    let settleTransaction = await instance.settle(new web3.BigNumber("0"), { "from": accounts[2] } );
    assert.web3Event(settleTransaction, {
      'event': 'TCRequestStatus',
      'args': {
        'TCRequestIDReturned': 2
      }
    });

    let mocksuccess = await mocker.mockSuccess();
    let mockedCallback = await mocker.fakeCallback({"from": accounts[0]});

    // accessing the derivativeSettled event programmatically is proving hard, but it IS firing, can tell when there's an error in the test, and also through coverage
    // assert.web3Event(mockedCallback.receipt, {
    //   'event': 'DerivativeSettled',
    //   'args': {
    //     'id': 6,
    //     'maker': accounts[1],
    //     'taker': accounts[2],
    //     'makerAmount': 10000000000000000,
    //     'takerAmount' : 20000000000000000,
    //     'triggerPrice': 50000,
    //     'actualPrice': 52,
    //     'triggerHeight': bn+3,
    //   }
    // });
    //console.log(mockedCallback.receipt.logs); 


    let afterSettleTakerValue = web3.eth.getBalance(accounts[2]);
    let afterSettleMakerValue = web3.eth.getBalance(accounts[1]);

    let settleTx = await web3.eth.getTransaction(settleTransaction.tx);
    gasCost = settleTx.gasPrice.mul(settleTransaction.receipt.gasUsed);
    assert.equal(
        afterSettleTakerValue.toNumber(),
        afterTakeTakerValue.minus(gasCost).toNumber(), // TC fee hard coded 75 rn, taker wins jackpot
        "Taker should lose the settle."
    )
    assert.equal(
        afterSettleMakerValue.toNumber(),
        afterMakeMakerValue.plus("20000000000000000").plus("10000000000000000").minus("7500000000000000").toNumber(), 
        "Maker should win the settle."
    ) 
  });

  it("should properly allow someone to mint, take, and settle tokens (Taker Wins)", async () => {
    let instance = await BTCGasTokenArtifact.deployed();
    let mocker = await MockTownCrierArtifact.deployed();
    let bn = web3.eth.blockNumber;
    var gasCost;

    let startingTakerAccountValue = web3.eth.getBalance(accounts[2]);
    let startingMakerAccountValue = web3.eth.getBalance(accounts[1]);

    let mintedTransaction = await instance.mint(new web3.BigNumber("20000000000000000"),  new web3.BigNumber("40"), new web3.BigNumber(bn+3), { "from": accounts[1],"value": ( new web3.BigNumber("10000000000000000" ) ) } ) ;

    let mintTx = await web3.eth.getTransaction(mintedTransaction.tx);
    gasCost = mintTx.gasPrice.mul(mintedTransaction.receipt.gasUsed);
    let afterMakeMakerValue = web3.eth.getBalance(accounts[1]);
    assert.equal(
        afterMakeMakerValue.toNumber(),
        ((startingMakerAccountValue.minus(gasCost).minus((new web3.BigNumber("10000000000000000")))).toNumber()),
        "Minting costs money, numbers don't match up."
    );


    let takenTransaction = await instance.take(new web3.BigNumber("1"), { "from": accounts[2], "value": new web3.BigNumber("20000000000000000") } );

    let takenTx = await web3.eth.getTransaction(takenTransaction.tx);
    gasCost = takenTx.gasPrice.mul(takenTransaction.receipt.gasUsed);
    let afterTakeTakerValue = web3.eth.getBalance(accounts[2]);
    assert.equal(
        afterTakeTakerValue.toNumber(),
        ((startingTakerAccountValue.minus(gasCost).minus((new web3.BigNumber("20000000000000000")))).toNumber()),
        "Taking costs money, numbers don't match up."
    );


    let settleTransaction = await instance.settle(new web3.BigNumber("1"), { "from": accounts[2] } );

    let mocksuccess = await mocker.mockSuccess();
    let mockedCallback = await mocker.fakeCallback({"from": accounts[0]});

    let afterSettleTakerValue = web3.eth.getBalance(accounts[2]);
    let afterSettleMakerValue = web3.eth.getBalance(accounts[1]);

    let settleTx = await web3.eth.getTransaction(settleTransaction.tx);
    gasCost = settleTx.gasPrice.mul(settleTransaction.receipt.gasUsed);
    assert.equal(
        afterSettleTakerValue.toNumber(),
        afterTakeTakerValue.plus("20000000000000000").plus("10000000000000000").minus("7500000000000000").minus(gasCost).toNumber(), // TC fee hard coded 75 rn, taker wins jackpot
        "Taker should win the settle. (minus gas cost minus TC fee)"
    )
    assert.equal(
        afterSettleMakerValue.toNumber(),
        afterMakeMakerValue.toNumber(), 
        "Maker should lose the settle. No change in account."
    ) 
  });

  it("should properly handle when town crier returns -252 saying that not enough TC Fee was sent", async () => {
    let instance = await BTCGasTokenArtifact.deployed();
    let mocker = await MockTownCrierArtifact.deployed();
    let bn = web3.eth.blockNumber;

    var gasCost;

    let mintedTransaction = await instance.mint(new web3.BigNumber("2000000000000000000"),  new web3.BigNumber("50000"), new web3.BigNumber(bn+3), { "from": accounts[3],"value": ( new web3.BigNumber("1000000000000000000" ) ) } ) ;
    let takenTransaction = await instance.take(new web3.BigNumber("2"), { "from": accounts[4], "value": new web3.BigNumber("2000000000000000000") } );

    let beforeSettleMaker = web3.eth.getBalance(accounts[3]);
    let beforeSettleTaker = web3.eth.getBalance(accounts[4]);

    let mockFail = await mocker.mockFailNotEnoughFee();

    let settleTransaction = await instance.settle(new web3.BigNumber("2"), { "from": accounts[4] } );
    assert.web3Event(settleTransaction, {
      'event': 'DerivativeError',
      'args': {
        'id': 2,
        'maker': accounts[3],
        'makerAmount': 1000000000000000000,
        'taker': accounts[4],
        'takerAmount' : 2000000000000000000,
        'triggerPrice': 50000,
        'triggerHeight': bn+3,
        'tcRequestId': -252
      }
    });

    let mockedCallback = await mocker.fakeCallback();

    let settleTx = await web3.eth.getTransaction(settleTransaction.tx);
    gasCost = settleTx.gasPrice.mul(settleTransaction.receipt.gasUsed);
    assert.equal(
        web3.eth.getBalance(accounts[4]).toNumber(),
        beforeSettleTaker.minus(gasCost).minus("7500000000000000").plus("2000000000000000000").toNumber(),
        "A failed settle should only cost the price of gas and the tc fee.");
    assert.equal(
        web3.eth.getBalance(accounts[3]).toNumber(),
        beforeSettleMaker.plus("1000000000000000000").toNumber(),
        "A failed settle should only cost the price of gas and in this case, the maker should be reimbursed fully since the taker submitted the transaction.");

  });

  it("should properly handle when town crier returns other non-fee related errors", async () => {
    let instance = await BTCGasTokenArtifact.deployed();
    let mocker = await MockTownCrierArtifact.deployed();
    let bn = web3.eth.blockNumber;

    var gasCost;

    let mintedTransaction = await instance.mint(new web3.BigNumber("2000000000000000000"),  new web3.BigNumber("50000"), new web3.BigNumber(bn+3), { "from": accounts[3],"value": ( new web3.BigNumber("1000000000000000000" ) ) } ) ;
    let takenTransaction = await instance.take(new web3.BigNumber("3"), { "from": accounts[4], "value": new web3.BigNumber("2000000000000000000") } );

    let beforeSettleMaker = web3.eth.getBalance(accounts[3]);
    let beforeSettleTaker = web3.eth.getBalance(accounts[4]);

    let mockFail = await mocker.mockFailUpgradedContract();

    let settleTransaction = await instance.settle(new web3.BigNumber("3"), { "from": accounts[4] } );
    assert.web3Event(settleTransaction, {
      'event': 'DerivativeError',
      'args': {
        'id': 3,
        'maker': accounts[3],
        'makerAmount': 1000000000000000000,
        'taker': accounts[4],
        'takerAmount' : 2000000000000000000,
        'triggerPrice': 50000,
        'triggerHeight': bn+3,
        'tcRequestId': -1152921504606847000
      }
    });

    let mockedCallback = await mocker.fakeCallback();

    let settleTx = await web3.eth.getTransaction(settleTransaction.tx);
    gasCost = settleTx.gasPrice.mul(settleTransaction.receipt.gasUsed);
    assert.equal(
        web3.eth.getBalance(accounts[4]).toNumber(),
        beforeSettleTaker.minus(gasCost).minus("7500000000000000").plus("2000000000000000000").toNumber(),
        "A failed settle should only cost the price of gas and the tc fee.");
    assert.equal(
        web3.eth.getBalance(accounts[3]).toNumber(),
        beforeSettleMaker.plus("1000000000000000000").toNumber(),
        "A failed settle should only cost the price of gas and in this case, the maker should be reimbursed fully since the taker submitted the transaction.");

  });
});


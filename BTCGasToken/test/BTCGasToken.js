require('truffle-test-utils').init();
var BigNumber = require('big-number');

var BTCGasTokenArtifact = artifacts.require("BTCGasToken");

contract('BTCGasToken', function(accounts) {

  // this test passes its just hella slow and unnecessary
  // it("should have a name and ticker that are proper", async () => {
  //   let instance = await BTCGasTokenArtifact.deployed();
  //   let retName = await instance.name();
  //   assert.equal(retName, "BTCFees by gastoken.io", "Name on contract does not match expected value");
  //   let retSymbol = await instance.symbol();
  //   assert.equal(retSymbol, "BTCF", "Symbol on contract does not match expected value");
  // });

  // let 0xae13B183f5a6aA1B4533C75c735E1594d2C3282A be an arbitrary address on rinkeby acting as the maker
  // let 0xaD57BD48bA5e5Ef8951CDC7442328120db6b094d be an arbitrary address on rinkeby acting as the taker
  // let  be an arbitrary address on rinkeby acting as the maker
  it("Should be able to mint a transaction", async () => {
    let instance = await BTCGasTokenArtifact.deployed();
    let mintedID = instance.mint(new BigNumber("20000000000000000"),  new BigNumber("50"), new BigNumber("2254128"), { "from":"0xae13B183f5a6aA1B4533C75c735E1594d2C3282A","value": ( new BigNumber("10000000000000000" ) ) } ) ;
    assert.isAbove(mintedID, 0, "Returned ID should be a positive number...");
    assert.web3Event(result, {
      'event': 'DerivativeCreated',
      'args': {
        'id': 1,
        'maker': "0xae13B183f5a6aA1B4533C75c735E1594d2C3282A",
        'makerAmount': "10000000000000000",
        'takerAmount' : "20000000000000000",
        'triggerPrice': "50",
        'triggerHeight': "2254128",
      }
    });
    // instance.take(mintedID, { "from":"0xad57bd48ba5e5ef8951cdc7442328120db6b094d","value": ( new BigNumber("20000000000000000" ) ) } ) ;
    // assert.web3Event(result, {
    //   'event': 'DerivativeTaken',
    //   'args': {
    //     'id': 1,
    //     'maker': "0xae13B183f5a6aA1B4533C75c735E1594d2C3282A",
    //     'taker': "0xad57bd48ba5e5ef8951cdc7442328120db6b094d",
    //     'makerAmount': "10000000000000000",
    //     'takerAmount' : "20000000000000000",
    //     'triggerPrice': "50",
    //     'triggerHeight': "2254128",
    //   }
    // });
  }); 

});

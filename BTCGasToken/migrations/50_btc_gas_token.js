var BTCGasTokenArtifact = artifacts.require("BTCGasToken");
var MockTownCrierArtifact = artifacts.require("MockTownCrier");

module.exports = function(deployer, network) {
  if(network == "rinkeby") {
    deployer.deploy(BTCGasTokenArtifact, "0x9eC1874FF1deF6E178126f7069487c2e9e93D0f9");
    return;
  } else {
    deployer.deploy(BTCGasTokenArtifact, MockTownCrierArtifact.address);
  }
}

var BTCGasTokenArtifact = artifacts.require("BTCGasToken");

module.exports = function(deployer) {
  deployer.deploy(BTCGasTokenArtifact, "0x9eC1874FF1deF6E178126f7069487c2e9e93D0f9");
}

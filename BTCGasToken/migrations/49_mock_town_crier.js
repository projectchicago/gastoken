var MockTownCrierArtifact = artifacts.require("MockTownCrier");
module.exports = function(deployer, network) {
  if(network == "development") {
      deployer.deploy(MockTownCrierArtifact);
  }
}

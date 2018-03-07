contract GST2 {
	function freeUpTo(uint256 value) public returns (uint256 freed);
	function freeFromUpTo(address from, uint256 value) public returns (uint256 freed);	
}

contract GST2FreeExample {
	function freeExample(uint num_tokens) public returns (uint freed) {
		// we need at least 
		//     num_tokens * (1148 + 5722 + 150) + 25710 gas before entering destroyChildren
		//                   ^ mk_contract_address   
		//                                        ^ solidity bug constant
		//                          ^ cost of invocation
		//                                 ^ loop, etc...
		// to be on the safe side, let's add another constant 2k gas
		// for CALLing freeFrom, reading from storage, etc...
		// so we get
		//     gas cost to freeFromUpTo n tokens <= 27710 + n * (1148 + 5722 + 150)
		
		// Note that 27710 is sufficiently large that we always have enough 
		// gas left to update s_tail, balance, etc... after we are done 
		// with destroyChildren.

		GST2 gst2 = GST2(0x0000000000b3F879cb30FE243b4Dfee438691c04);

		uint safe_num_tokens = 0;
		uint gas = msg.gas;

		if (gas >= 27710) {
			safe_num_tokens = (gas - 27710) / (1148 + 5722 + 150);
		}

		if (num_tokens > safe_num_tokens) {
			num_tokens = safe_num_tokens;
		}

		if (num_tokens > 0) {
			return gst2.freeUpTo(num_tokens);
		} else {
			return 0;
		}
	}

	function freeFromExample(address from, uint num_tokens) public returns (uint freed) {
		// we need at least 
		//     num_tokens * (1148 + 5722 + 150) + 25710 gas before entering destroyChildren
		//                   ^ mk_contract_address   
		//                                        ^ solidity bug constant
		//                          ^ cost of invocation
		//                                 ^ loop, etc...
		// to be on the safe side, let's add another constant 2k gas
		// for CALLing freeFrom, reading from storage, etc...
		// so we get
		//     gas cost to freeFromUpTo n tokens <= 27710 + n * (1148 + 5722 + 150)
		
		// Note that 27710 is sufficiently large that we always have enough 
		// gas left to update s_tail, balance, etc... after we are done 
		// with destroyChildren.

		GST2 gst2 = GST2(0x0000000000b3F879cb30FE243b4Dfee438691c04);
		
		uint safe_num_tokens = 0;
		uint gas = msg.gas;

		if (gas >= 27710) {
			safe_num_tokens = (gas - 27710) / (1148 + 5722 + 150);
		}

		if (num_tokens > safe_num_tokens) {
			num_tokens = safe_num_tokens;
		}

		if (num_tokens > 0) {
			return gst2.freeFromUpTo(from, num_tokens);
		} else {
			return 0;
		}
	}
}

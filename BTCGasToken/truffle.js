module.exports = {
    networks: {
        development: {
            host: "127.0.0.1",
            port: 9545,
            network_id: "*" // Match any network id
        },
        rinkeby: {
            host: "localhost", // Connect to geth on the specified
            port: 8088,
            from: "0xFFe7642922f0F6010291acd934bb18F174aaa218", // default address to use for any transaction Truffle makes during migrations
            network_id: 4,
            gas: 3610000 // Gas limit used for deploys
        }
    }
};

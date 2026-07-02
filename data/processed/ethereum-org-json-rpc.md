---
{
  "project": "ethereum",
  "source_url": "https://ethereum.org/en/developers/docs/apis/json-rpc/",
  "consent_proof": "",
  "ingested_at": 1760356893,
  "user_agent": "agentic-web3-rag/0.1 (+https://github.com/you/agentic-web3-rag)",
  "policy_mode": "allowlist_only"
}
---

JSON-RPC API
In order for a software application to interact with the Ethereum blockchain - either by reading blockchain data or sending transactions to the network - it must connect to an Ethereum node.
For this purpose, every Ethereum client implements a JSON-RPC specification, so there is a uniform set of methods that applications can rely on regardless of the specific node or client implementation.
JSON-RPC is a stateless, light-weight remote procedure call (RPC) protocol. It defines several data structures and the rules around their processing. It is transport agnostic in that the concepts can be used within the same process, over sockets, over HTTP, or in many various message passing environments. It uses JSON (RFC 4627) as data format.
Client implementations
Ethereum clients each may utilize different programming languages when implementing the JSON-RPC specification. See individual client documentation for further details related to specific programming languages. We recommend checking the documentation of each client for the latest API support information.
Convenience Libraries
While you may choose to interact directly with Ethereum clients via the JSON-RPC API, there are often easier options for dapp developers. Many JavaScript and backend API libraries exist to provide wrappers on top of the JSON-RPC API. With these libraries, developers can write intuitive, one-line methods in the programming language of their choice to initialize JSON-RPC requests (under the hood) that interact with Ethereum.
Consensus client APIs
This page deals mainly with the JSON-RPC API used by Ethereum execution clients. However, consensus clients also have an RPC API that allows users to query information about the node, request Beacon blocks, Beacon state, and other consensus-related information directly from a node. This API is documented on the Beacon API webpage.
An internal API is also used for inter-client communication within a node - that is, it enables the consensus client and execution client to swap data. This is called the 'Engine API' and the specs are available on GitHub.
Execution client spec
Read the full JSON-RPC API spec on GitHub. This API is documented on the Execution API webpage and includes an Inspector to try out all the available methods.
Conventions
Hex value encoding
Two key data types get passed over JSON: unformatted byte arrays and quantities. Both are passed with a hex encoding but with different requirements for formatting.
Quantities
When encoding quantities (integers, numbers): encode as hex, prefix with "0x", the most compact representation (slight exception: zero should be represented as "0x0").
Here are some examples:
- 0x41 (65 in decimal)
- 0x400 (1024 in decimal)
- WRONG: 0x (should always have at least one digit - zero is "0x0")
- WRONG: 0x0400 (no leading zeroes allowed)
- WRONG: ff (must be prefixed 0x)
Unformatted data
When encoding unformatted data (byte arrays, account addresses, hashes, bytecode arrays): encode as hex, prefix with "0x", two hex digits per byte.
Here are some examples:
- 0x41 (size 1, "A")
- 0x004200 (size 3, "0B0")
- 0x (size 0, "")
- WRONG: 0xf0f0f (must be even number of digits)
- WRONG: 004200 (must be prefixed 0x)
The block parameter
The following methods have a block parameter:
When requests are made that query the state of Ethereum, the provided block parameter determines the height of the block.
The following options are possible for the block parameter:
HEX String
- an integer block numberString "earliest"
for the earliest/genesis blockString "latest"
- for the latest proposed blockString "safe"
- for the latest safe head blockString "finalized"
- for the latest finalized blockString "pending"
- for the pending state/transactions
Examples
On this page we provide examples of how to use individual JSON_RPC API endpoints using the command line tool, curl. These individual endpoint examples are found below in the Curl examples section. Further down the page, we also provide an end-to-end example for compiling and deploying a smart contract using a Geth node, the JSON_RPC API and curl.
Curl examples
Examples of using the JSON_RPC API by making curl requests to an Ethereum node are provided below. Each example includes a description of the specific endpoint, its parameters, return type, and a worked example of how it should be used.
The curl requests might return an error message relating to the content type. This is because the --data
option sets the content type to application/x-www-form-urlencoded
. If your node does complain about this, manually set the header by placing -H "Content-Type: application/json"
at the start of the call. The examples also do not include the URL/IP & port combination which must be the last argument given to curl (e.g. 127.0.0.1:8545
). A complete curl request including these additional data takes the following form:
1curl -H "Content-Type: application/json" -X POST --data '{"jsonrpc":"2.0","method":"web3_clientVersion","params":[],"id":67}' 127.0.0.1:8545
Gossip, State, History
A handful of core JSON-RPC methods require data from the Ethereum network, and fall neatly into three main categories: Gossip, State, and History. Use the links in these sections to jump to each method, or use the table of contents to explore the whole list of methods.
Gossip Methods
These methods track the head of the chain. This is how transactions make their way around the network, find their way into blocks, and how clients find out about new blocks.
State Methods
Methods that report the current state of all the data stored. The "state" is like one big shared piece of RAM, and includes account balances, contract data, and gas estimations.
History Methods
Fetches historical records of every block back to genesis. This is like one large append-only file, and includes all block headers, block bodies, uncle blocks, and transaction receipts.
- eth_getBlockTransactionCountByHash
- eth_getBlockTransactionCountByNumber
- eth_getUncleCountByBlockHash
- eth_getUncleCountByBlockNumber
- eth_getBlockByHash
- eth_getBlockByNumber
- eth_getTransactionByHash
- eth_getTransactionByBlockHashAndIndex
- eth_getTransactionByBlockNumberAndIndex
- eth_getTransactionReceipt
- eth_getUncleByBlockHashAndIndex
- eth_getUncleByBlockNumberAndIndex
JSON-RPC API Playground
You can use the playground tool to discover and try out the API methods. It also shows you which methods and networks are supported by various node providers.
JSON-RPC API Methods
web3_clientVersion
Returns the current client version.
Parameters
None
Returns
String
- The current client version
Example
1// Request2curl -X POST --data '{"jsonrpc":"2.0","method":"web3_clientVersion","params":[],"id":67}'3// Result4{5 "id":67,6 "jsonrpc":"2.0",7 "result": "Geth/v1.12.1-stable/linux-amd64/go1.19.1"8}
web3_sha3
Returns Keccak-256 (not the standardized SHA3-256) of the given data.
Parameters
DATA
- The data to convert into a SHA3 hash
1params: ["0x68656c6c6f20776f726c64"]
Returns
DATA
- The SHA3 result of the given string.
Example
1// Request2curl -X POST --data '{"jsonrpc":"2.0","method":"web3_sha3","params":["0x68656c6c6f20776f726c64"],"id":64}'3// Result4{5 "id":64,6 "jsonrpc": "2.0",7 "result": "0x47173285a8d7341e5e972fc677286384f802f8ef42a5ec5f03bbfa254cb01fad"8}
net_version
Returns the current network id.
Parameters
None
Returns
String
- The current network id.
The full list of current network IDs is available at chainlist.org. Some common ones are:
1
: Ethereum Mainnet11155111
: Sepolia testnet560048
: Hoodi Testnet
Example
1// Request2curl -X POST --data '{"jsonrpc":"2.0","method":"net_version","params":[],"id":67}'3// Result4{5 "id":67,6 "jsonrpc": "2.0",7 "result": "3"8}
net_listening
Returns true
if client is actively listening for network connections.
Parameters
None
Returns
Boolean
- true
when listening, otherwise false
.
Example
1// Request2curl -X POST --data '{"jsonrpc":"2.0","method":"net_listening","params":[],"id":67}'3// Result4{5 "id":67,6 "jsonrpc":"2.0",7 "result":true8}
net_peerCount
Returns number of peers currently connected to the client.
Parameters
None
Returns
QUANTITY
- integer of the number of connected peers.
Example
1// Request2curl -X POST --data '{"jsonrpc":"2.0","method":"net_peerCount","params":[],"id":74}'3// Result4{5 "id":74,6 "jsonrpc": "2.0",7 "result": "0x2" // 28}
eth_protocolVersion
Returns the current Ethereum protocol version. Note that this method is not available in Geth.
Parameters
None
Returns
String
- The current Ethereum protocol version
Example
1// Request2curl -X POST --data '{"jsonrpc":"2.0","method":"eth_protocolVersion","params":[],"id":67}'3// Result4{5 "id":67,6 "jsonrpc": "2.0",7 "result": "54"8}
eth_syncing
Returns an object with data about the sync status or false
.
Parameters
None
Returns
The precise return data varies between client implementations. All clients return False
when the node is not syncing, and all clients return the following fields.
Object|Boolean
, An object with sync status data or FALSE
, when not syncing:
startingBlock
:QUANTITY
- The block at which the import started (will only be reset, after the sync reached his head)currentBlock
:QUANTITY
- The current block, same as eth_blockNumberhighestBlock
:QUANTITY
- The estimated highest block
However, the individual clients may also provide additional data. For example Geth returns the following:
1{2 "jsonrpc": "2.0",3 "id": 1,4 "result": {5 "currentBlock": "0x3cf522",6 "healedBytecodeBytes": "0x0",7 "healedBytecodes": "0x0",8 "healedTrienodes": "0x0",9 "healingBytecode": "0x0",10 "healingTrienodes": "0x0",11 "highestBlock": "0x3e0e41",12 "startingBlock": "0x3cbed5",13 "syncedAccountBytes": "0x0",14 "syncedAccounts": "0x0",15 "syncedBytecodeBytes": "0x0",16 "syncedBytecodes": "0x0",17 "syncedStorage": "0x0",18 "syncedStorageBytes": "0x0"19 }20}Show all
Whereas Besu returns:
1{2 "jsonrpc": "2.0",3 "id": 51,4 "result": {5 "startingBlock": "0x0",6 "currentBlock": "0x1518",7 "highestBlock": "0x9567a3",8 "pulledStates": "0x203ca",9 "knownStates": "0x200636"10 }11}Show all
Refer to the documentation for your specific client for more details.
Example
1// Request2curl -X POST --data '{"jsonrpc":"2.0","method":"eth_syncing","params":[],"id":1}'3// Result4{5 "id":1,6 "jsonrpc": "2.0",7 "result": {8 startingBlock: '0x384',9 currentBlock: '0x386',10 highestBlock: '0x454'11 }12}13// Or when not syncing14{15 "id":1,16 "jsonrpc": "2.0",17 "result": false18}Show all
eth_coinbase
Returns the client coinbase address.
Try endpoint in playgroundNote: This method has been deprecated as of v1.14.0 and is no longer supported. Attempting to use this method will result in a "Method not supported" error.
Parameters
None
Returns
DATA
, 20 bytes - the current coinbase address.
Example
1// Request2curl -X POST --data '{"jsonrpc":"2.0","method":"eth_coinbase","params":[],"id":64}'3// Result4{5 "id":64,6 "jsonrpc": "2.0",7 "result": "0x407d73d8a49eeb85d32cf465507dd71d507100c1"8}
eth_chainId
Returns the chain ID used for signing replay-protected transactions.
Try endpoint in playgroundParameters
None
Returns
chainId
, hexadecimal value as a string representing the integer of the current chain id.
Example
1// Request2curl -X POST --data '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":67}'3// Result4{5 "id":67,6 "jsonrpc": "2.0",7 "result": "0x1"8}
eth_mining
Returns true
if client is actively mining new blocks. This can only return true
for proof-of-work networks and may not be available in some clients since The Merge.
Parameters
None
Returns
Boolean
- returns true
if the client is mining, otherwise false
.
Example
1// Request2curl -X POST --data '{"jsonrpc":"2.0","method":"eth_mining","params":[],"id":71}'3//4{5 "id":71,6 "jsonrpc": "2.0",7 "result": true8}
eth_hashrate
Returns the number of hashes per second that the node is mining with. This can only return true
for proof-of-work networks and may not be available in some clients since The Merge.
Parameters
None
Returns
QUANTITY
- number of hashes per second.
Example
1// Request2curl -X POST --data '{"jsonrpc":"2.0","method":"eth_hashrate","params":[],"id":71}'3// Result4{5 "id":71,6 "jsonrpc": "2.0",7 "result": "0x38a"8}
eth_gasPrice
Returns an estimate of the current price per gas in wei. For example, the Besu client examines the last 100 blocks and returns the median gas unit price by default.
Try endpoint in playgroundParameters
None
Returns
QUANTITY
- integer of the current gas price in wei.
Example
1// Request2curl -X POST --data '{"jsonrpc":"2.0","method":"eth_gasPrice","params":[],"id":73}'3// Result4{5 "id":73,6 "jsonrpc": "2.0",7 "result": "0x1dfd14000" // 8049999872 Wei8}
eth_accounts
Returns a list of addresses owned by client.
Try endpoint in playgroundParameters
None
Returns
Array of DATA
, 20 Bytes - addresses owned by the client.
Example
1// Request2curl -X POST --data '{"jsonrpc":"2.0","method":"eth_accounts","params":[],"id":1}'3// Result4{5 "id":1,6 "jsonrpc": "2.0",7 "result": ["0x407d73d8a49eeb85d32cf465507dd71d507100c1"]8}
eth_blockNumber
Returns the number of most recent block.
Try endpoint in playgroundParameters
None
Returns
QUANTITY
- integer of the current block number the client is on.
Example
1// Request2curl -X POST --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":83}'3// Result4{5 "id":83,6 "jsonrpc": "2.0",7 "result": "0x4b7" // 12078}
eth_getBalance
Returns the balance of the account of given address.
Try endpoint in playgroundParameters
DATA
, 20 Bytes - address to check for balance.QUANTITY|TAG
- integer block number, or the string"latest"
,"earliest"
,"pending"
,"safe"
, or"finalized"
, see the block parameter
1params: ["0x407d73d8a49eeb85d32cf465507dd71d507100c1", "latest"]
Returns
QUANTITY
- integer of the current balance in wei.
Example
1// Request2curl -X POST --data '{"jsonrpc":"2.0","method":"eth_getBalance","params":["0x407d73d8a49eeb85d32cf465507dd71d507100c1", "latest"],"id":1}'3// Result4{5 "id":1,6 "jsonrpc": "2.0",7 "result": "0x0234c8a3397aab58" // 1589724902343750008}
eth_getStorageAt
Returns the value from a storage position at a given address.
Try endpoint in playgroundParameters
DATA
, 20 Bytes - address of the storage.QUANTITY
- integer of the position in the storage.QUANTITY|TAG
- integer block number, or the string"latest"
,"earliest"
,"pending"
,"safe"
,"finalized"
, see the block parameter
Returns
DATA
- the value at this storage position.
Example
Calculating the correct position depends on the storage to retrieve. Consider the following contract deployed at 0x295a70b2de5e3953354a6a8344e616ed314d7251
by address 0x391694e7e0b0cce554cb130d723a9d27458f9298
.
1contract Storage {2 uint pos0;3 mapping(address => uint) pos1;4 constructor() {5 pos0 = 1234;6 pos1[msg.sender] = 5678;7 }8}
Retrieving the value of pos0 is straight forward:
1curl -X POST --data '{"jsonrpc":"2.0", "method": "eth_getStorageAt", "params": ["0x295a70b2de5e3953354a6a8344e616ed314d7251", "0x0", "latest"], "id": 1}' localhost:85452{"jsonrpc":"2.0","id":1,"result":"0x00000000000000000000000000000000000000000000000000000000000004d2"}
Retrieving an element of the map is harder. The position of an element in the map is calculated with:
1keccak(LeftPad32(key, 0), LeftPad32(map position, 0))
This means to retrieve the storage on pos1["0x391694e7e0b0cce554cb130d723a9d27458f9298"] we need to calculate the position with:
1keccak(2 decodeHex(3 "000000000000000000000000391694e7e0b0cce554cb130d723a9d27458f9298" +4 "0000000000000000000000000000000000000000000000000000000000000001"5 )6)
The geth console which comes with the web3 library can be used to make the calculation:
1> var key = "000000000000000000000000391694e7e0b0cce554cb130d723a9d27458f9298" + "0000000000000000000000000000000000000000000000000000000000000001"2undefined3> web3.sha3(key, {"encoding": "hex"})4"0x6661e9d6d8b923d5bbaab1b96e1dd51ff6ea2a93520fdc9eb75d059238b8c5e9"
Now to fetch the storage:
1curl -X POST --data '{"jsonrpc":"2.0", "method": "eth_getStorageAt", "params": ["0x295a70b2de5e3953354a6a8344e616ed314d7251", "0x6661e9d6d8b923d5bbaab1b96e1dd51ff6ea2a93520fdc9eb75d059238b8c5e9", "latest"], "id": 1}' localhost:85452{"jsonrpc":"2.0","id":1,"result":"0x000000000000000000000000000000000000000000000000000000000000162e"}
eth_getTransactionCount
Returns the number of transactions sent from an address.
Try endpoint in playgroundParameters
DATA
, 20 Bytes - address.QUANTITY|TAG
- integer block number, or the string"latest"
,"earliest"
,"pending"
,"safe"
or"finalized"
, see the block parameter
1params: [2 "0x407d73d8a49eeb85d32cf465507dd71d507100c1",3 "latest", // state at the latest block4]
Returns
QUANTITY
- integer of the number of transactions send from this address.
Example
1// Request2curl -X POST --data '{"jsonrpc":"2.0","method":"eth_getTransactionCount","params":["0x407d73d8a49eeb85d32cf465507dd71d507100c1","latest"],"id":1}'3// Result4{5 "id":1,6 "jsonrpc": "2.0",7 "result": "0x1" // 18}
eth_getBlockTransactionCountByHash
Returns the number of transactions in a block from a block matching the given block hash.
Try endpoint in playgroundParameters
DATA
, 32 Bytes - hash of a block
1params: ["0xd03ededb7415d22ae8bac30f96b2d1de83119632693b963642318d87d1bece5b"]
Returns
QUANTITY
- integer of the number of transactions in this block.
Example
1// Request2curl -X POST --data '{"jsonrpc":"2.0","method":"eth_getBlockTransactionCountByHash","params":["0xd03ededb7415d22ae8bac30f96b2d1de83119632693b963642318d87d1bece5b"],"id":1}'3// Result4{5 "id":1,6 "jsonrpc": "2.0",7 "result": "0x8b" // 1398}
eth_getBlockTransactionCountByNumber
Returns the number of transactions in a block matching the given block number.
Try endpoint in playgroundParameters
QUANTITY|TAG
- integer of a block number, or the string"earliest"
,"latest"
,"pending"
,"safe"
or"finalized"
, as in the block parameter.
1params: [2 "0x13738ca", // 203962343]
Returns
QUANTITY
- integer of the number of transactions in this block.
Example
1// Request2curl -X POST --data '{"jsonrpc":"2.0","method":"eth_getBlockTransactionCountByNumber","params":["0x13738ca"],"id":1}'3// Result4{5 "id":1,6 "jsonrpc": "2.0",7 "result": "0x8b" // 1398}
eth_getUncleCountByBlockHash
Returns the number of uncles in a block from a block matching the given block hash.
Try endpoint in playgroundParameters
DATA
, 32 Bytes - hash of a block
1params: ["0x1d59ff54b1eb26b013ce3cb5fc9dab3705b415a67127a003c3e61eb445bb8df2"]
Returns
QUANTITY
- integer of the number of uncles in this block.
Example
1// Request2curl -X POST --data '{"jsonrpc":"2.0","method":"eth_getUncleCountByBlockHash","params":["0x1d59ff54b1eb26b013ce3cb5fc9dab3705b415a67127a003c3e61eb445bb8df2"],"id":1}'3// Result4{5 "id":1,6 "jsonrpc": "2.0",7 "result": "0x1" // 18}
eth_getUncleCountByBlockNumber
Returns the number of uncles in a block from a block matching the given block number.
Try endpoint in playgroundParameters
QUANTITY|TAG
- integer of a block number, or the string"latest"
,"earliest"
,"pending"
,"safe"
or"finalized"
, see the block parameter
1params: [2 "0xe8", // 2323]
Returns
QUANTITY
- integer of the number of uncles in this block.
Example
1// Request2curl -X POST --data '{"jsonrpc":"2.0","method":"eth_getUncleCountByBlockNumber","params":["0xe8"],"id":1}'3// Result4{5 "id":1,6 "jsonrpc": "2.0",7 "result": "0x0" // 08}
eth_getCode
Returns code at a given address.
Try endpoint in playgroundParameters
DATA
, 20 Bytes - addressQUANTITY|TAG
- integer block number, or the string"latest"
,"earliest"
,"pending"
,"safe"
or"finalized"
, see the block parameter
1params: [2 "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",3 "0x5daf3b", // 61397074]
Returns
DATA
- the code from the given address.
Example
1// Request2curl -X POST --data '{"jsonrpc":"2.0","method":"eth_getCode","params":["0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", "0x5daf3b"],"id":1}'3// Result4{5 "id":1,6 "jsonrpc": "2.0",7 "result": "0x6060604052600436106100af576000357c0100000000000000000000000000000000000000000000000000000000900463ffffffff16806306fdde03146100b9578063095ea7b31461014757806318160ddd146101a157806323b872dd146101ca5780632e1a7d4d14610243578063313ce5671461026657806370a082311461029557806395d89b41146102e2578063a9059cbb14610370578063d0e30db0146103ca578063dd62ed3e146103d4575b6100b7610440565b005b34156100c457600080fd5b6100cc6104dd565b6040518080602001828103825283818151815260200191508051906020019080838360005b8381101561010c5780820151818401526020810190506100f1565b50505050905090810190601f1680156101395780820380516001836020036101000a031916815260200191505b509250505060405180910390f35b341561015257600080fd5b610187600480803573ffffffffffffffffffffffffffffffffffffffff1690602001909190803590602001909190505061057b565b604051808215151515815260200191505060405180910390f35b34156101ac57600080fd5b6101b461066d565b6040518082815260200191505060405180910390f35b34156101d557600080fd5b610229600480803573ffffffffffffffffffffffffffffffffffffffff1690602001909190803573ffffffffffffffffffffffffffffffffffffffff1690602001909190803590602001909190505061068c565b604051808215151515815260200191505060405180910390f35b341561024e57600080fd5b61026460048080359060200190919050506109d9565b005b341561027157600080fd5b610279610b05565b604051808260ff1660ff16815260200191505060405180910390f35b34156102a057600080fd5b6102cc600480803573ffffffffffffffffffffffffffffffffffffffff16906020019091905050610b18565b6040518082815260200191505060405180910390f35b34156102ed57600080fd5b6102f5610b30565b6040518080602001828103825283818151815260200191508051906020019080838360005b8381101561033557808201518184015260208101905061031a565b50505050905090810190601f1680156103625780820380516001836020036101000a031916815260200191505b509250505060405180910390f35b341561037b57600080fd5b6103b0600480803573ffffffffffffffffffffffffffffffffffffffff16906020019091908035906020019091905050610bce565b604051808215151515815260200191505060405180910390f35b6103d2610440565b005b34156103df57600080fd5b61042a600480803573ffffffffffffffffffffffffffffffffffffffff1690602001909190803573ffffffffffffffffffffffffffffffffffffffff16906020019091905050610be3565b6040518082815260200191505060405180910390f35b34600360003373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff168152602001908152602001600020600082825401925050819055503373ffffffffffffffffffffffffffffffffffffffff167fe1fffcc4923d04b559f4d29a8bfc6cda04eb5b0d3c460751c2402c5c5cc9109c346040518082815260200191505060405180910390a2565b60008054600181600116156101000203166002900480601f0160208091040260200160405190810160405280929190818152602001828054600181600116156101000203166002900480156105735780601f1061054857610100808354040283529160200191610573565b820191906000526020600020905b81548152906001019060200180831161055657829003601f168201915b505050505081565b600081600460003373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff16815260200190815260200160002060008573ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff168152602001908152602001600020819055508273ffffffffffffffffffffffffffffffffffffffff163373ffffffffffffffffffffffffffffffffffffffff167f8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925846040518082815260200191505060405180910390a36001905092915050565b60003073ffffffffffffffffffffffffffffffffffffffff1631905090565b600081600360008673ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff16815260200190815260200160002054101515156106dc57600080fd5b3373ffffffffffffffffffffffffffffffffffffffff168473ffffffffffffffffffffffffffffffffffffffff16141580156107b457507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff600460008673ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff16815260200190815260200160002060003373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff1681526020019081526020016000205414155b156108cf5781600460008673ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff16815260200190815260200160002060003373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff168152602001908152602001600020541015151561084457600080fd5b81600460008673ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff16815260200190815260200160002060003373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff168152602001908152602001600020600082825403925050819055505b81600360008673ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff1681526020019081526020016000206000828254039250508190555081600360008573ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff168152602001908152602001600020600082825401925050819055508273ffffffffffffffffffffffffffffffffffffffff168473ffffffffffffffffffffffffffffffffffffffff167fddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef846040518082815260200191505060405180910390a3600190509392505050565b80600360003373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff1681526020019081526020016000205410151515610a2757600080fd5b80600360003373ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff168152602001908152602001600020600082825403925050819055503373ffffffffffffffffffffffffffffffffffffffff166108fc829081150290604051600060405180830381858888f193505050501515610ab457600080fd5b3373ffffffffffffffffffffffffffffffffffffffff167f7fcf532c15f0a6db0bd6d0e038bea71d30d808c7d98cb3bf7268a95bf5081b65826040518082815260200191505060405180910390a250565b600260009054906101000a900460ff1681565b60036020528060005260406000206000915090505481565b60018054600181600116156101000203166002900480601f016020809104026020016040519081016040528092919081815260200182805460018160011615610100020316600290048015610bc65780601f10610b9b57610100808354040283529160200191610bc6565b820191906000526020600020905b815481529060010190602001808311610ba957829003601f168201915b505050505081565b6000610bdb33848461068c565b905092915050565b60046020528160005260406000206020528060005260406000206000915091505054815600a165627a7a72305820deb4c2ccab3c2fdca32ab3f46728389c2fe2c165d5fafa07661e4e004f6c344a0029"8}
eth_sign
The sign method calculates an Ethereum specific signature with: sign(keccak256("\x19Ethereum Signed Message:\n" + len(message) + message)))
.
By adding a prefix to the message makes the calculated signature recognizable as an Ethereum specific signature. This prevents misuse where a malicious dapp can sign arbitrary data (e.g. transaction) and use the signature to impersonate the victim.
Note: the address to sign with must be unlocked.
Parameters
DATA
, 20 Bytes - addressDATA
, N Bytes - message to sign
Returns
DATA
: Signature
Example
1// Request2curl -X POST --data '{"jsonrpc":"2.0","method":"eth_sign","params":["0x9b2055d370f73ec7d8a03e965129118dc8f5bf83", "0xdeadbeaf"],"id":1}'3// Result4{5 "id":1,6 "jsonrpc": "2.0",7 "result": "0xa3f20717a250c2b0b729b7e5becbff67fdaef7e0699da4de7ca5895b02a170a12d887fd3b17bfdce3481f10bea41f45ba9f709d39ce8325427b57afcfc994cee1b"8}
eth_signTransaction
Signs a transaction that can be submitted to the network at a later time using with eth_sendRawTransaction.
Parameters
Object
- The transaction object
type
:from
:DATA
, 20 Bytes - The address the transaction is sent from.to
:DATA
, 20 Bytes - (optional when creating new contract) The address the transaction is directed to.gas
:QUANTITY
- (optional, default: 90000) Integer of the gas provided for the transaction execution. It will return unused gas.gasPrice
:QUANTITY
- (optional, default: To-Be-Determined) Integer of the gasPrice used for each paid gas, in Wei.value
:QUANTITY
- (optional) Integer of the value sent with this transaction, in Wei.data
:DATA
- The compiled code of a contract OR the hash of the invoked method signature and encoded parameters.nonce
:QUANTITY
- (optional) Integer of a nonce. This allows to overwrite your own pending transactions that use the same nonce.
Returns
DATA
, The RLP-encoded transaction object signed by the specified account.
Example
1// Request2curl -X POST --data '{"id": 1,"jsonrpc": "2.0","method": "eth_signTransaction","params": [{"data":"0xd46e8dd67c5d32be8d46e8dd67c5d32be8058bb8eb970870f072445675058bb8eb970870f072445675","from": "0xb60e8dd61c5d32be8058bb8eb970870f07233155","gas": "0x76c0","gasPrice": "0x9184e72a000","to": "0xd46e8dd67c5d32be8058bb8eb970870f07244567","value": "0x9184e72a"}]}'3// Result4{5 "id": 1,6 "jsonrpc": "2.0",7 "result": "0xa3f20717a250c2b0b729b7e5becbff67fdaef7e0699da4de7ca5895b02a170a12d887fd3b17bfdce3481f10bea41f45ba9f709d39ce8325427b57afcfc994cee1b"8}
eth_sendTransaction
Creates new message call transaction or a contract creation, if the data field contains code, and signs it using the account specified in from
.
Parameters
Object
- The transaction object
from
:DATA
, 20 Bytes - The address the transaction is sent from.to
:DATA
, 20 Bytes - (optional when creating new contract) The address the transaction is directed to.gas
:QUANTITY
- (optional, default: 90000) Integer of the gas provided for the transaction execution. It will return unused gas.gasPrice
:QUANTITY
- (optional, default: To-Be-Determined) Integer of the gasPrice used for each paid gas.value
:QUANTITY
- (optional) Integer of the value sent with this transaction.input
:DATA
- The compiled code of a contract OR the hash of the invoked method signature and encoded parameters.nonce
:QUANTITY
- (optional) Integer of a nonce. This allows to overwrite your own pending transactions that use the same nonce.
1params: [2 {3 from: "0xb60e8dd61c5d32be8058bb8eb970870f07233155",4 to: "0xd46e8dd67c5d32be8058bb8eb970870f07244567",5 gas: "0x76c0", // 304006 gasPrice: "0x9184e72a000", // 100000000000007 value: "0x9184e72a", // 24414062508 input:9 "0xd46e8dd67c5d32be8d46e8dd67c5d32be8058bb8eb970870f072445675058bb8eb970870f072445675",10 },11]Show all
Returns
DATA
, 32 Bytes - the transaction hash, or the zero hash if the transaction is not yet available.
Use eth_getTransactionReceipt to get the contract address, after the transaction was proposed in a block, when you created a contract.
Example
1// Request2curl -X POST --data '{"jsonrpc":"2.0","method":"eth_sendTransaction","params":[{see above}],"id":1}'3// Result4{5 "id":1,6 "jsonrpc": "2.0",7 "result": "0xe670ec64341771606e55d6b4ca35a1a6b75ee3d5145a99d05921026d1527331"8}
eth_sendRawTransaction
Creates new message call transaction or a contract creation for signed transactions.
Parameters
DATA
, The signed transaction data.
1params: [2 "0xd46e8dd67c5d32be8d46e8dd67c5d32be8058bb8eb970870f072445675058bb8eb970870f072445675",3]
Returns
DATA
, 32 Bytes - the transaction hash, or the zero hash if the transaction is not yet available.
Use eth_getTransactionReceipt to get the contract address, after the transaction was proposed in a block, when you created a contract.
Example
1// Request2curl -X POST --data '{"jsonrpc":"2.0","method":"eth_sendRawTransaction","params":[{see above}],"id":1}'3// Result4{5 "id":1,6 "jsonrpc": "2.0",7 "result": "0xe670ec64341771606e55d6b4ca35a1a6b75ee3d5145a99d05921026d1527331"8}
eth_call
Executes a new message call immediately without creating a transaction on the blockchain. Often used for executing read-only smart contract functions, for example the balanceOf
for an ERC-20 contract.
Parameters
Object
- The transaction call object
from
:DATA
, 20 Bytes - (optional) The address the transaction is sent from.to
:DATA
, 20 Bytes - The address the transaction is directed to.gas
:QUANTITY
- (optional) Integer of the gas provided for the transaction execution. eth_call consumes zero gas, but this parameter may be needed by some executions.gasPrice
:QUANTITY
- (optional) Integer of the gasPrice used for each paid gasvalue
:QUANTITY
- (optional) Integer of the value sent with this transactioninput
:DATA
- (optional) Hash of the method signature and encoded parameters. For details see Ethereum Contract ABI in the Solidity documentation.
QUANTITY|TAG
- integer block number, or the string"latest"
,"earliest"
,"pending"
,"safe"
or"finalized"
, see the block parameter
Returns
DATA
- the return value of executed contract.
Example
1// Request2curl -X POST --data '{"jsonrpc":"2.0","method":"eth_call","params":[{see above}],"id":1}'3// Result4{5 "id":1,6 "jsonrpc": "2.0",7 "result": "0x"8}
eth_estimateGas
Generates and returns an estimate of how much gas is necessary to allow the transaction to complete. The transaction will not be added to the blockchain. Note that the estimate may be significantly more than the amount of gas actually used by the transaction, for a variety of reasons including EVM mechanics and node performance.
Try endpoint in playgroundParameters
See eth_call parameters, except that all properties are optional. If no gas limit is specified geth uses the block gas limit from the pending block as an upper bound. As a result the returned estimate might not be enough to executed the call/transaction when the amount of gas is higher than the pending block gas limit.
Returns
QUANTITY
- the amount of gas used.
Example
1// Request2curl -X POST --data '{"jsonrpc":"2.0","method":"eth_estimateGas","params":[{see above}],"id":1}'3// Result4{5 "id":1,6 "jsonrpc": "2.0",7 "result": "0x5208" // 210008}
eth_getBlockByHash
Returns information about a block by hash.
Try endpoint in playgroundParameters
DATA
, 32 Bytes - Hash of a block.Boolean
- Iftrue
it returns the full transaction objects, iffalse
only the hashes of the transactions.
1params: [2 "0xdc0818cf78f21a8e70579cb46a43643f78291264dda342ae31049421c82d21ae",3 false,4]
Returns
Object
- A block object, or null
when no block was found:
number
:QUANTITY
- the block number.null
when its pending block.hash
:DATA
, 32 Bytes - hash of the block.null
when its pending block.parentHash
:DATA
, 32 Bytes - hash of the parent block.nonce
:DATA
, 8 Bytes - hash of the generated proof-of-work.null
when its pending block,0x0
for proof-of-stake blocks (since The Merge)sha3Uncles
:DATA
, 32 Bytes - SHA3 of the uncles data in the block.logsBloom
:DATA
, 256 Bytes - the bloom filter for the logs of the block.null
when its pending block.transactionsRoot
:DATA
, 32 Bytes - the root of the transaction trie of the block.stateRoot
:DATA
, 32 Bytes - the root of the final state trie of the block.receiptsRoot
:DATA
, 32 Bytes - the root of the receipts trie of the block.miner
:DATA
, 20 Bytes - the address of the beneficiary to whom the block rewards were given.difficulty
:QUANTITY
- integer of the difficulty for this block.totalDifficulty
:QUANTITY
- integer of the total difficulty of the chain until this block.extraData
:DATA
- the "extra data" field of this block.size
:QUANTITY
- integer the size of this block in bytes.gasLimit
:QUANTITY
- the maximum gas allowed in this block.gasUsed
:QUANTITY
- the total used gas by all transactions in this block.timestamp
:QUANTITY
- the unix timestamp for when the block was collated.transactions
:Array
- Array of transaction objects, or 32 Bytes transaction hashes depending on the last given parameter.uncles
:Array
- Array of uncle hashes.
Example
1// Request2curl -X POST --data '{"jsonrpc":"2.0","method":"eth_getBlockByHash","params":["0xdc0818cf78f21a8e70579cb46a43643f78291264dda342ae31049421c82d21ae", false],"id":1}'3// Result4{5{6"jsonrpc": "2.0",7"id": 1,8"result": {9 "difficulty": "0x4ea3f27bc",10 "extraData": "0x476574682f4c5649562f76312e302e302f6c696e75782f676f312e342e32",11 "gasLimit": "0x1388",12 "gasUsed": "0x0",13 "hash": "0xdc0818cf78f21a8e70579cb46a43643f78291264dda342ae31049421c82d21ae",14 "logsBloom": "0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",15 "miner": "0xbb7b8287f3f0a933474a79eae42cbca977791171",16 "mixHash": "0x4fffe9ae21f1c9e15207b1f472d5bbdd68c9595d461666602f2be20daf5e7843",17 "nonce": "0x689056015818adbe",18 "number": "0x1b4",19 "parentHash": "0xe99e022112df268087ea7eafaf4790497fd21dbeeb6bd7a1721df161a6657a54",20 "receiptsRoot": "0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421",21 "sha3Uncles": "0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347",22 "size": "0x220",23 "stateRoot": "0xddc8b0234c2e0cad087c8b389aa7ef01f7d79b2570bccb77ce48648aa61c904d",24 "timestamp": "0x55ba467c",25 "totalDifficulty": "0x78ed983323d",26 "transactions": [27 ],28 "transactionsRoot": "0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421",29 "uncles": [30 ]31}32}Show all
eth_getBlockByNumber
Returns information about a block by block number.
Try endpoint in playgroundParameters
QUANTITY|TAG
- integer of a block number, or the string"earliest"
,"latest"
,"pending"
,"safe"
or"finalized"
, as in the block parameter.Boolean
- Iftrue
it returns the full transaction objects, iffalse
only the hashes of the transactions.
1params: [2 "0x1b4", // 4363 true,4]
Returns See eth_getBlockByHash
Example
1// Request2curl -X POST --data '{"jsonrpc":"2.0","method":"eth_getBlockByNumber","params":["0x1b4", true],"id":1}'
Result see eth_getBlockByHash
eth_getTransactionByHash
Returns the information about a transaction requested by transaction hash.
Try endpoint in playgroundParameters
DATA
, 32 Bytes - hash of a transaction
1params: ["0x88df016429689c079f3b2f6ad39fa052532c56795b733da78a91ebe6a713944b"]
Returns
Object
- A transaction object, or null
when no transaction was found:
blockHash
:DATA
, 32 Bytes - hash of the block where this transaction was in.null
when its pending.blockNumber
:QUANTITY
- block number where this transaction was in.null
when its pending.from
:DATA
, 20 Bytes - address of the sender.gas
:QUANTITY
- gas provided by the sender.gasPrice
:QUANTITY
- gas price provided by the sender in Wei.hash
:DATA
, 32 Bytes - hash of the transaction.input
:DATA
- the data send along with the transaction.nonce
:QUANTITY
- the number of transactions made by the sender prior to this one.to
:DATA
, 20 Bytes - address of the receiver.null
when its a contract creation transaction.transactionIndex
:QUANTITY
- integer of the transactions index position in the block.null
when its pending.value
:QUANTITY
- value transferred in Wei.v
:QUANTITY
- ECDSA recovery idr
:QUANTITY
- ECDSA signature rs
:QUANTITY
- ECDSA signature s
Example
1// Request2curl -X POST --data '{"jsonrpc":"2.0","method":"eth_getTransactionByHash","params":["0x88df016429689c079f3b2f6ad39fa052532c56795b733da78a91ebe6a713944b"],"id":1}'3// Result4{5 "jsonrpc":"2.0",6 "id":1,7 "result":{8 "blockHash":"0x1d59ff54b1eb26b013ce3cb5fc9dab3705b415a67127a003c3e61eb445bb8df2",9 "blockNumber":"0x5daf3b", // 613970710 "from":"0xa7d9ddbe1f17865597fbd27ec712455208b6b76d",11 "gas":"0xc350", // 5000012 "gasPrice":"0x4a817c800", // 2000000000013 "hash":"0x88df016429689c079f3b2f6ad39fa052532c56795b733da78a91ebe6a713944b",14 "input":"0x68656c6c6f21",15 "nonce":"0x15", // 2116 "to":"0xf02c1c8e6114b1dbe8937a39260b5b0a374432bb",17 "transactionIndex":"0x41", // 6518 "value":"0xf3dbb76162000", // 429000000000000019 "v":"0x25", // 3720 "r":"0x1b5e176d927f8e9ab405058b2d2457392da3e20f328b16ddabcebc33eaac5fea",21 "s":"0x4ba69724e8f69de52f0125ad8b3c5c2cef33019bac3249e2c0a2192766d1721c"22 }23}Show all
eth_getTransactionByBlockHashAndIndex
Returns information about a transaction by block hash and transaction index position.
Try endpoint in playgroundParameters
DATA
, 32 Bytes - hash of a block.QUANTITY
- integer of the transaction index position.
1params: [2 "0x1d59ff54b1eb26b013ce3cb5fc9dab3705b415a67127a003c3e61eb445bb8df2",3 "0x0", // 04]
Returns See eth_getTransactionByHash
Example
1// Request2curl -X POST --data '{"jsonrpc":"2.0","method":"eth_getTransactionByBlockHashAndIndex","params":["0x1d59ff54b1eb26b013ce3cb5fc9dab3705b415a67127a003c3e61eb445bb8df2", "0x0"],"id":1}'
Result see eth_getTransactionByHash
eth_getTransactionByBlockNumberAndIndex
Returns information about a transaction by block number and transaction index position.
Try endpoint in playgroundParameters
QUANTITY|TAG
- a block number, or the string"earliest"
,"latest"
,"pending"
,"safe"
or"finalized"
, as in the block parameter.QUANTITY
- the transaction index position.
1params: [2 "0x9c47cf", // 102419993 "0x24", // 364]
Returns See eth_getTransactionByHash
Example
1// Request2curl -X POST --data '{"jsonrpc":"2.0","method":"eth_getTransactionByBlockNumberAndIndex","params":["0x9c47cf", "0x24"],"id":1}'
Result see eth_getTransactionByHash
eth_getTransactionReceipt
Returns the receipt of a transaction by transaction hash.
Note That the receipt is not available for pending transactions.
Parameters
DATA
, 32 Bytes - hash of a transaction
1params: ["0x85d995eba9763907fdf35cd2034144dd9d53ce32cbec21349d4b12823c6860c5"]
Returns
Object
- A transaction receipt object, or null
when no receipt was found:
transactionHash
:DATA
, 32 Bytes - hash of the transaction.transactionIndex
:QUANTITY
- integer of the transactions index position in the block.blockHash
:DATA
, 32 Bytes - hash of the block where this transaction was in.blockNumber
:QUANTITY
- block number where this transaction was in.from
:DATA
, 20 Bytes - address of the sender.to
:DATA
, 20 Bytes - address of the receiver. null when its a contract creation transaction.cumulativeGasUsed
:QUANTITY
- The total amount of gas used when this transaction was executed in the block.effectiveGasPrice
:QUANTITY
- The sum of the base fee and tip paid per unit of gas.gasUsed
:QUANTITY
- The amount of gas used by this specific transaction alone.contractAddress
:DATA
, 20 Bytes - The contract address created, if the transaction was a contract creation, otherwisenull
.logs
:Array
- Array of log objects, which this transaction generated.logsBloom
:DATA
, 256 Bytes - Bloom filter for light clients to quickly retrieve related logs.type
:QUANTITY
- integer of the transaction type,0x0
for legacy transactions,0x1
for access list types,0x2
for dynamic fees.
It also returns either :
root
:DATA
32 bytes of post-transaction stateroot (pre Byzantium)status
:QUANTITY
either1
(success) or0
(failure)
Example
1// Request2curl -X POST --data '{"jsonrpc":"2.0","method":"eth_getTransactionReceipt","params":["0x85d995eba9763907fdf35cd2034144dd9d53ce32cbec21349d4b12823c6860c5"],"id":1}'3// Result4{5 "jsonrpc": "2.0",6 "id": 1,7 "result": {8 "blockHash":9 "0xa957d47df264a31badc3ae823e10ac1d444b098d9b73d204c40426e57f47e8c3",10 "blockNumber": "0xeff35f",11 "contractAddress": null, // string of the address if it was created12 "cumulativeGasUsed": "0xa12515",13 "effectiveGasPrice": "0x5a9c688d4",14 "from": "0x6221a9c005f6e47eb398fd867784cacfdcfff4e7",15 "gasUsed": "0xb4c8",16 "logs": [{17 // logs as returned by getFilterLogs, etc.18 }],19 "logsBloom": "0x00...0", // 256 byte bloom filter20 "status": "0x1",21 "to": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",22 "transactionHash":23 "0x85d995eba9763907fdf35cd2034144dd9d53ce32cbec21349d4b12823c6860c5",24 "transactionIndex": "0x66",25 "type": "0x2"26 }27}Show all
eth_getUncleByBlockHashAndIndex
Returns information about a uncle of a block by hash and uncle index position.
Try endpoint in playgroundParameters
DATA
, 32 Bytes - The hash of a block.QUANTITY
- The uncle's index position.
1params: [2 "0x1d59ff54b1eb26b013ce3cb5fc9dab3705b415a67127a003c3e61eb445bb8df2",3 "0x0", // 04]
Returns See eth_getBlockByHash
Example
1// Request2curl -X POST --data '{"jsonrpc":"2.0","method":"eth_getUncleByBlockHashAndIndex","params":["0x1d59ff54b1eb26b013ce3cb5fc9dab3705b415a67127a003c3e61eb445bb8df2", "0x0"],"id":1}'
Result see eth_getBlockByHash
Note: An uncle doesn't contain individual transactions.
eth_getUncleByBlockNumberAndIndex
Returns information about a uncle of a block by number and uncle index position.
Try endpoint in playgroundParameters
QUANTITY|TAG
- a block number, or the string"earliest"
,"latest"
,"pending"
,"safe"
,"finalized"
, as in the block parameter.QUANTITY
- the uncle's index position.
1params: [2 "0x29c", // 6683 "0x0", // 04]
Returns See eth_getBlockByHash
Note: An uncle doesn't contain individual transactions.
Example
1// Request2curl -X POST --data '{"jsonrpc":"2.0","method":"eth_getUncleByBlockNumberAndIndex","params":["0x29c", "0x0"],"id":1}'
Result see eth_getBlockByHash
eth_newFilter
Creates a filter object, based on filter options, to notify when the state changes (logs). To check if the state has changed, call eth_getFilterChanges.
A note on specifying topic filters: Topics are order-dependent. A transaction with a log with topics [A, B] will be matched by the following topic filters:
[]
"anything"[A]
"A in first position (and anything after)"[null, B]
"anything in first position AND B in second position (and anything after)"[A, B]
"A in first position AND B in second position (and anything after)"[[A, B], [A, B]]
"(A OR B) in first position AND (A OR B) in second position (and anything after)"- Parameters
Object
- The filter options:
fromBlock
:QUANTITY|TAG
- (optional, default:"latest"
) Integer block number, or"latest"
for the last proposed block,"safe"
for the latest safe block,"finalized"
for the latest finalized block, or"pending"
,"earliest"
for transactions not yet in a block.toBlock
:QUANTITY|TAG
- (optional, default:"latest"
) Integer block number, or"latest"
for the last proposed block,"safe"
for the latest safe block,"finalized"
for the latest finalized block, or"pending"
,"earliest"
for transactions not yet in a block.address
:DATA|Array
, 20 Bytes - (optional) Contract address or a list of addresses from which logs should originate.topics
:Array of DATA
, - (optional) Array of 32 BytesDATA
topics. Topics are order-dependent. Each topic can also be an array of DATA with "or" options.
1params: [2 {3 fromBlock: "0x1",4 toBlock: "0x2",5 address: "0x8888f1f195afa192cfee860698584c030f4c9db1",6 topics: [7 "0x000000000000000000000000a94f5374fce5edbc8e2a8697c15331677e6ebf0b",8 null,9 [10 "0x000000000000000000000000a94f5374fce5edbc8e2a8697c15331677e6ebf0b",11 "0x0000000000000000000000000aff3454fce5edbc8cca8697c15331677e6ebccc",12 ],13 ],14 },15]Show all
Returns
QUANTITY
- A filter id.
Example
1// Request2curl -X POST --data '{"jsonrpc":"2.0","method":"eth_newFilter","params":[{"topics":["0x12341234"]}],"id":73}'3// Result4{5 "id":1,6 "jsonrpc": "2.0",7 "result": "0x1" // 18}
eth_newBlockFilter
Creates a filter in the node, to notify when a new block arrives. To check if the state has changed, call eth_getFilterChanges.
Parameters None
Returns
QUANTITY
- A filter id.
Example
1// Request2curl -X POST --data '{"jsonrpc":"2.0","method":"eth_newBlockFilter","params":[],"id":73}'3// Result4{5 "id":1,6 "jsonrpc": "2.0",7 "result": "0x1" // 18}
eth_newPendingTransactionFilter
Creates a filter in the node, to notify when new pending transactions arrive. To check if the state has changed, call eth_getFilterChanges.
Parameters None
Returns
QUANTITY
- A filter id.
Example
1// Request2curl -X POST --data '{"jsonrpc":"2.0","method":"eth_newPendingTransactionFilter","params":[],"id":73}'3// Result4{5 "id":1,6 "jsonrpc": "2.0",7 "result": "0x1" // 18}
eth_uninstallFilter
Uninstalls a filter with given id. Should always be called when watch is no longer needed. Additionally Filters timeout when they aren't requested with eth_getFilterChanges for a period of time.
Parameters
QUANTITY
- The filter id.
1params: [2 "0xb", // 113]
Returns
Boolean
- true
if the filter was successfully uninstalled, otherwise false
.
Example
1// Request2curl -X POST --data '{"jsonrpc":"2.0","method":"eth_uninstallFilter","params":["0xb"],"id":73}'3// Result4{5 "id":1,6 "jsonrpc": "2.0",7 "result": true8}
eth_getFilterChanges
Polling method for a filter, which returns an array of logs which occurred since last poll.
Parameters
QUANTITY
- the filter id.
1params: [2 "0x16", // 223]
Returns
Array
- Array of log objects, or an empty array if nothing has changed since last poll.
- For filters created with
eth_newBlockFilter
the return are block hashes (DATA
, 32 Bytes), e.g.["0x3454645634534..."]
. - For filters created with
eth_newPendingTransactionFilter
the return are transaction hashes (DATA
, 32 Bytes), e.g.["0x6345343454645..."]
. - For filters created with
eth_newFilter
logs are objects with following params:removed
:TAG
-true
when the log was removed, due to a chain reorganization.false
if its a valid log.logIndex
:QUANTITY
- integer of the log index position in the block.null
when its pending log.transactionIndex
:QUANTITY
- integer of the transactions index position log was created from.null
when its pending log.transactionHash
:DATA
, 32 Bytes - hash of the transactions this log was created from.null
when its pending log.blockHash
:DATA
, 32 Bytes - hash of the block where this log was in.null
when its pending.null
when its pending log.blockNumber
:QUANTITY
- the block number where this log was in.null
when its pending.null
when its pending log.address
:DATA
, 20 Bytes - address from which this log originated.data
:DATA
- contains zero or more 32 Bytes non-indexed arguments of the log.topics
:Array of DATA
- Array of 0 to 4 32 BytesDATA
of indexed log arguments. (In solidity: The first topic is the hash of the signature of the event (e.g.Deposit(address,bytes32,uint256)
), except you declared the event with theanonymous
specifier.)
- Example
1// Request2curl -X POST --data '{"jsonrpc":"2.0","method":"eth_getFilterChanges","params":["0x16"],"id":73}'3// Result4{5 "id":1,6 "jsonrpc":"2.0",7 "result": [{8 "logIndex": "0x1", // 19 "blockNumber":"0x1b4", // 43610 "blockHash": "0x8216c5785ac562ff41e2dcfdf5785ac562ff41e2dcfdf829c5a142f1fccd7d",11 "transactionHash": "0xdf829c5a142f1fccd7d8216c5785ac562ff41e2dcfdf5785ac562ff41e2dcf",12 "transactionIndex": "0x0", // 013 "address": "0x16c5785ac562ff41e2dcfdf829c5a142f1fccd7d",14 "data":"0x0000000000000000000000000000000000000000000000000000000000000000",15 "topics": ["0x59ebeb90bc63057b6515673c3ecf9438e5058bca0f92585014eced636878c9a5"]16 },{17 ...18 }]19}Show all
eth_getFilterLogs
Returns an array of all logs matching filter with given id.
Parameters
QUANTITY
- The filter id.
1params: [2 "0x16", // 223]
Returns See eth_getFilterChanges
Example
1// Request2curl -X POST --data '{"jsonrpc":"2.0","method":"eth_getFilterLogs","params":["0x16"],"id":74}'
Result see eth_getFilterChanges
eth_getLogs
Returns an array of all logs matching a given filter object.
Parameters
Object
- The filter options:
fromBlock
:QUANTITY|TAG
- (optional, default:"latest"
) Integer block number, or"latest"
for the last proposed block,"safe"
for the latest safe block,"finalized"
for the latest finalized block, or"pending"
,"earliest"
for transactions not yet in a block.toBlock
:QUANTITY|TAG
- (optional, default:"latest"
) Integer block number, or"latest"
for the last proposed block,"safe"
for the latest safe block,"finalized"
for the latest finalized block, or"pending"
,"earliest"
for transactions not yet in a block.address
:DATA|Array
, 20 Bytes - (optional) Contract address or a list of addresses from which logs should originate.topics
:Array of DATA
, - (optional) Array of 32 BytesDATA
topics. Topics are order-dependent. Each topic can also be an array of DATA with "or" options.blockHash
:DATA
, 32 Bytes - (optional, future) With the addition of EIP-234,blockHash
will be a new filter option which restricts the logs returned to the single block with the 32-byte hashblockHash
. UsingblockHash
is equivalent tofromBlock
=toBlock
= the block number with hashblockHash
. IfblockHash
is present in the filter criteria, then neitherfromBlock
nortoBlock
are allowed.
1params: [2 {3 topics: [4 "0x000000000000000000000000a94f5374fce5edbc8e2a8697c15331677e6ebf0b",5 ],6 },7]
Returns See eth_getFilterChanges
Example
1// Request2curl -X POST --data '{"jsonrpc":"2.0","method":"eth_getLogs","params":[{"topics":["0x000000000000000000000000a94f5374fce5edbc8e2a8697c15331677e6ebf0b"]}],"id":74}'
Result see eth_getFilterChanges
Usage Example
Deploying a contract using JSON_RPC
This section includes a demonstration of how to deploy a contract using only the RPC interface. There are alternative routes to deploying contracts where this complexity is abstracted away—for example, using libraries built on top of the RPC interface such as web3.js and web3.py. These abstractions are generally easier to understand and less error-prone, but it is still helpful to understand what is happening under the hood.
The following is a straightforward smart contract called Multiply7
that will be deployed using the JSON-RPC interface to an Ethereum node. This tutorial assumes the reader is already running a Geth node. More information on nodes and clients is available here. Please refer to individual client documentation to see how to start the HTTP JSON-RPC for non-Geth clients. Most clients default to serving on localhost:8545
.
1contract Multiply7 {2 event Print(uint);3 function multiply(uint input) returns (uint) {4 Print(input * 7);5 return input * 7;6 }7}
The first thing to do is make sure the HTTP RPC interface is enabled. This means we supply Geth with the --http
flag on startup. In this example we use the Geth node on a private development chain. Using this approach we don't need ether on the real network.
geth --http --dev console 2>>geth.log
This will start the HTTP RPC interface on http://localhost:8545
.
We can verify that the interface is running by retrieving the coinbase address (by obtaining the first address from the array of accounts) and balance using curl. Please note that data in these examples will differ on your local node. If you want to try these commands, replace the request params in the second curl request with the result returned from the first.
curl --data '{"jsonrpc":"2.0","method":"eth_accounts","params":[]", "id":1}' -H "Content-Type: application/json" localhost:8545{"id":1,"jsonrpc":"2.0","result":["0x9b1d35635cc34752ca54713bb99d38614f63c955"]}curl --data '{"jsonrpc":"2.0","method":"eth_getBalance", "params": ["0x9b1d35635cc34752ca54713bb99d38614f63c955", "latest"], "id":2}' -H "Content-Type: application/json" localhost:8545{"id":2,"jsonrpc":"2.0","result":"0x1639e49bba16280000"}
Because numbers are hex encoded, the balance is returned in wei as a hex string. If we want to have the balance in ether as a number we can use web3 from the Geth console.
1web3.fromWei("0x1639e49bba16280000", "ether")2// "410"
Now that there is some ether on our private development chain, we can deploy the contract. The first step is to compile the Multiply7 contract to byte code that can be sent to the EVM. To install solc, the Solidity compiler, follow the Solidity documentation. (You might want to use an older solc
release to match the version of compiler used for our example.)
The next step is to compile the Multiply7 contract to byte code that can be send to the EVM.
echo 'pragma solidity ^0.4.16; contract Multiply7 { event Print(uint); function multiply(uint input) public returns (uint) { Print(input * 7); return input * 7; } }' | solc --bin======= <stdin>:Multiply7 =======Binary:6060604052341561000f57600080fd5b60eb8061001d6000396000f300606060405260043610603f576000357c0100000000000000000000000000000000000000000000000000000000900463ffffffff168063c6888fa1146044575b600080fd5b3415604e57600080fd5b606260048080359060200190919050506078565b6040518082815260200191505060405180910390f35b60007f24abdb5865df5079dcc5ac590ff6f01d5c16edbc5fab4e195d9febd1114503da600783026040518082815260200191505060405180910390a16007820290509190505600a165627a7a7230582040383f19d9f65246752244189b02f56e8d0980ed44e7a56c0b200458caad20bb0029
Now that we have the compiled code we need to determine how much gas it costs to deploy it. The RPC interface has an eth_estimateGas
method that will give us an estimate.
curl --data '{"jsonrpc":"2.0","method": "eth_estimateGas", "params": [{"from": "0x9b1d35635cc34752ca54713bb99d38614f63c955", "data": "0x6060604052341561000f57600080fd5b60eb8061001d6000396000f300606060405260043610603f576000357c0100000000000000000000000000000000000000000000000000000000900463ffffffff168063c6888fa1146044575b600080fd5b3415604e57600080fd5b606260048080359060200190919050506078565b6040518082815260200191505060405180910390f35b60007f24abdb5865df5079dcc5ac590ff6f01d5c16edbc5fab4e195d9febd1114503da600783026040518082815260200191505060405180910390a16007820290509190505600a165627a7a7230582040383f19d9f65246752244189b02f56e8d0980ed44e7a56c0b200458caad20bb0029"}], "id": 5}' -H "Content-Type: application/json" localhost:8545{"jsonrpc":"2.0","id":5,"result":"0x1c31e"}
And finally deploy the contract.
curl --data '{"jsonrpc":"2.0","method": "eth_sendTransaction", "params": [{"from": "0x9b1d35635cc34752ca54713bb99d38614f63c955", "gas": "0x1c31e", "data": "0x6060604052341561000f57600080fd5b60eb8061001d6000396000f300606060405260043610603f576000357c0100000000000000000000000000000000000000000000000000000000900463ffffffff168063c6888fa1146044575b600080fd5b3415604e57600080fd5b606260048080359060200190919050506078565b6040518082815260200191505060405180910390f35b60007f24abdb5865df5079dcc5ac590ff6f01d5c16edbc5fab4e195d9febd1114503da600783026040518082815260200191505060405180910390a16007820290509190505600a165627a7a7230582040383f19d9f65246752244189b02f56e8d0980ed44e7a56c0b200458caad20bb0029"}], "id": 6}' -H "Content-Type: application/json" localhost:8545{"id":6,"jsonrpc":"2.0","result":"0xe1f3095770633ab2b18081658bad475439f6a08c902d0915903bafff06e6febf"}
The transaction is accepted by the node and a transaction hash is returned. This hash can be used to track the transaction. The next step is to determine the address where our contract is deployed. Each executed transaction will create a receipt. This receipt contains various information about the transaction such as in which block the transaction was included and how much gas was used by the EVM. If a transaction
creates a contract it will also contain the contract address. We can retrieve the receipt with the eth_getTransactionReceipt
RPC method.
curl --data '{"jsonrpc":"2.0","method": "eth_getTransactionReceipt", "params": ["0xe1f3095770633ab2b18081658bad475439f6a08c902d0915903bafff06e6febf"], "id": 7}' -H "Content-Type: application/json" localhost:8545{"jsonrpc":"2.0","id":7,"result":{"blockHash":"0x77b1a4f6872b9066312de3744f60020cbd8102af68b1f6512a05b7619d527a4f","blockNumber":"0x1","contractAddress":"0x4d03d617d700cf81935d7f797f4e2ae719648262","cumulativeGasUsed":"0x1c31e","from":"0x9b1d35635cc34752ca54713bb99d38614f63c955","gasUsed":"0x1c31e","logs":[],"logsBloom":"0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000","status":"0x1","to":null,"transactionHash":"0xe1f3095770633ab2b18081658bad475439f6a08c902d0915903bafff06e6febf","transactionIndex":"0x0"}}
Our contract was created on 0x4d03d617d700cf81935d7f797f4e2ae719648262
. A null result instead of a receipt means the transaction has not been included in a block yet. Wait for a moment and check if your consensus client is running and retry it.
Interacting with smart contracts
In this example we will be sending a transaction using eth_sendTransaction
to the multiply
method of the contract.
eth_sendTransaction
requires several arguments, specifically from
, to
and data
. From
is the public address of our account, and to
is the contract address. The data
argument contains a payload that defines which method must be called and with which arguments. This is where the ABI (application binary interface) comes into play. The ABI is a JSON file that defines how to define and encode data for the EVM.
The bytes of the payload defines which method in the contract is called. This is the first 4 bytes from the Keccak hash over the function name and its argument types, hex encoded. The multiply function accepts an uint which is an alias for uint256. This leaves us with:
1web3.sha3("multiply(uint256)").substring(0, 10)2// "0xc6888fa1"
The next step is to encode the arguments. There is only one uint256, say, the value 6. The ABI has a section which specifies how to encode uint256 types.
int<M>: enc(X)
is the big-endian two’s complement encoding of X, padded on the higher-order (left) side with 0xff for negative X and with zero > bytes for positive X such that the length is a multiple of 32 bytes.
This encodes to 0000000000000000000000000000000000000000000000000000000000000006
.
Combining the function selector and the encoded argument our data will be 0xc6888fa10000000000000000000000000000000000000000000000000000000000000006
.
This can now be sent to the node:
curl --data '{"jsonrpc":"2.0","method": "eth_sendTransaction", "params": [{"from": "0xeb85a5557e5bdc18ee1934a89d8bb402398ee26a", "to": "0x6ff93b4b46b41c0c3c9baee01c255d3b4675963d", "data": "0xc6888fa10000000000000000000000000000000000000000000000000000000000000006"}], "id": 8}' -H "Content-Type: application/json" localhost:8545{"id":8,"jsonrpc":"2.0","result":"0x759cf065cbc22e9d779748dc53763854e5376eea07409e590c990eafc0869d74"}
Since a transaction was sent, a transaction hash was returned. Retrieving the receipt gives:
1{2 blockHash: "0xbf0a347307b8c63dd8c1d3d7cbdc0b463e6e7c9bf0a35be40393588242f01d55",3 blockNumber: 268,4 contractAddress: null,5 cumulativeGasUsed: 22631,6 gasUsed: 22631,7 logs: [{8 address: "0x6ff93b4b46b41c0c3c9baee01c255d3b4675963d",9 blockHash: "0xbf0a347307b8c63dd8c1d3d7cbdc0b463e6e7c9bf0a35be40393588242f01d55",10 blockNumber: 268,11 data: "0x000000000000000000000000000000000000000000000000000000000000002a",12 logIndex: 0,13 topics: ["0x24abdb5865df5079dcc5ac590ff6f01d5c16edbc5fab4e195d9febd1114503da"],14 transactionHash: "0x759cf065cbc22e9d779748dc53763854e5376eea07409e590c990eafc0869d74",15 transactionIndex: 016 }],17 transactionHash: "0x759cf065cbc22e9d779748dc53763854e5376eea07409e590c990eafc0869d74",18 transactionIndex: 019}Show all
The receipt contains a log. This log was generated by the EVM on transaction execution and included in the receipt. The multiply
function shows that the Print
event was raised with the input times 7. Since the argument for the Print
event was a uint256 we can decode it according to the ABI rules which will leave us with the expected decimal 42. Apart from the data it is worth noting that topics can be used to determine which event created the log:
1web3.sha3("Print(uint256)")2// "24abdb5865df5079dcc5ac590ff6f01d5c16edbc5fab4e195d9febd1114503da"
This was just a brief introduction into some of the most common tasks, demonstrating direct usage of the JSON-RPC.

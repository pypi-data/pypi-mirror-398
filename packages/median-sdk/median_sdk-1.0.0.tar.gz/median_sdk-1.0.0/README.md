# Median Blockchain Python SDK

Python SDK for interacting with the Median blockchain, providing easy-to-use interfaces for account management, coin operations, and inference task management.

## Features

- **Account Management**: Create and query blockchain accounts dynamically
- **Coin Operations**: Mint and burn tokens with proper authorization
- **Task Management**: Create inference tasks with commit-reveal consensus
- **Query Functionality**: Query blockchain state, balances, and task results
- **Type-Safe**: Uses dataclasses and type hints for better IDE support

## Installation

### Requirements

- Python 3.7 or higher
- `requests` library

### Install Dependencies

```bash
pip install requests
```

### Install SDK

Copy the `median_sdk.py` file to your project or add the SDK directory to your Python path:

```python
import sys
sys.path.insert(0, '/path/to/Median/sdk/python')
from median_sdk import MedianSDK, Coin, create_sdk
```

## Quick Start

```python
from median_sdk import create_sdk, Coin

# Initialize the SDK
sdk = create_sdk(api_url="http://localhost:1317", chain_id="median")

# Query an account balance
balance = sdk.get_account_balance("cosmos16tzn8wytv7srdw6v9l4q7ncmu8a092wrrfjp7l")
for coin in balance:
    print(f"{coin.amount} {coin.denom}")

# Get blockchain info
node_info = sdk.get_node_info()
print(f"Chain ID: {node_info['default_node_info']['network']}")
```

## API Reference

### Initialization

#### `MedianSDK(api_url, chain_id, timeout)`

Initialize the SDK with blockchain connection parameters.

**Parameters:**
- `api_url` (str): Base URL of the blockchain API (default: "http://localhost:1317")
- `chain_id` (str): Chain ID (default: "median")
- `timeout` (int): Request timeout in seconds (default: 30)

**Example:**
```python
sdk = MedianSDK(
    api_url="http://localhost:1317",
    chain_id="median",
    timeout=30
)
```

### Account Management

#### `create_account(creator_address, new_account_address, private_key=None)`

Create a new blockchain account dynamically.

**Parameters:**
- `creator_address` (str): Address of the account creator (must have authority)
- `new_account_address` (str): Address for the new account
- `private_key` (str, optional): Private key for signing transactions

**Returns:** Transaction response dictionary

**Example:**
```python
result = sdk.create_account(
    creator_address="cosmos10d07y265gmmuvt4z0w9aw880jnsr700j6zn9kn",
    new_account_address="cosmos1newaccount123..."
)
```

#### `get_account(address)`

Get account information by address.

**Parameters:**
- `address` (str): Account address

**Returns:** Account information dictionary

**Example:**
```python
account = sdk.get_account("cosmos16tzn8wytv7srdw6v9l4q7ncmu8a092wrrfjp7l")
print(account['account']['@type'])
```

#### `get_account_balance(address)`

Get account balance.

**Parameters:**
- `address` (str): Account address

**Returns:** List of `Coin` objects

**Example:**
```python
balances = sdk.get_account_balance("cosmos16tzn8wytv7srdw6v9l4q7ncmu8a092wrrfjp7l")
for coin in balances:
    print(f"{coin.amount} {coin.denom}")
```

### Coin Management

#### `mint_coins(authority_address, recipient_address, amount, private_key=None)`

Mint new coins and send to recipient.

**Parameters:**
- `authority_address` (str): Address with minting authority
- `recipient_address` (str): Address to receive minted coins
- `amount` (List[Coin]): List of coins to mint
- `private_key` (str, optional): Private key for signing

**Returns:** Transaction response dictionary

**Example:**
```python
from median_sdk import Coin

result = sdk.mint_coins(
    authority_address="cosmos10d07y265gmmuvt4z0w9aw880jnsr700j6zn9kn",
    recipient_address="cosmos16tzn8wytv7srdw6v9l4q7ncmu8a092wrrfjp7l",
    amount=[
        Coin(denom="token", amount="1000"),
        Coin(denom="stake", amount="5000")
    ]
)
```

#### `burn_coins(authority_address, amount, from_address="", private_key=None)`

Burn coins from the module account.

**Parameters:**
- `authority_address` (str): Address with burning authority
- `amount` (List[Coin]): List of coins to burn
- `from_address` (str, optional): Source address (currently only module account supported)
- `private_key` (str, optional): Private key for signing

**Returns:** Transaction response dictionary

**Example:**
```python
result = sdk.burn_coins(
    authority_address="cosmos10d07y265gmmuvt4z0w9aw880jnsr700j6zn9kn",
    amount=[Coin(denom="token", amount="500")]
)
```

### Task Management

#### `create_task(creator_address, task_id, description, input_data, private_key=None)`

Create a new inference task.

**Parameters:**
- `creator_address` (str): Address of the task creator
- `task_id` (str): Unique identifier for the task
- `description` (str): Task description
- `input_data` (str): Input data for the task
- `private_key` (str, optional): Private key for signing

**Returns:** Transaction response dictionary

**Example:**
```python
result = sdk.create_task(
    creator_address="cosmos16tzn8wytv7srdw6v9l4q7ncmu8a092wrrfjp7l",
    task_id="task_001",
    description="Predict BTC price",
    input_data="Current price: $50000"
)
```

#### `commit_result(validator_address, task_id, result, nonce, private_key=None)`

Commit a result hash for a task (commit phase of commit-reveal).

**Parameters:**
- `validator_address` (str): Address of the validator
- `task_id` (str): Task identifier
- `result` (int): The actual result value
- `nonce` (int): Random nonce to prevent hash collision
- `private_key` (str, optional): Private key for signing

**Returns:** Transaction response dictionary

**Example:**
```python
import random

result = 52000  # Predicted value
nonce = random.randint(1000000, 9999999)

commit_response = sdk.commit_result(
    validator_address="cosmos16tzn8wytv7srdw6v9l4q7ncmu8a092wrrfjp7l",
    task_id="task_001",
    result=result,
    nonce=nonce
)
```

#### `reveal_result(validator_address, task_id, result, nonce, private_key=None)`

Reveal the actual result for a task (reveal phase of commit-reveal).

**Parameters:**
- `validator_address` (str): Address of the validator
- `task_id` (str): Task identifier
- `result` (int): The actual result value (must match commit)
- `nonce` (int): Nonce used in commit phase (must match commit)
- `private_key` (str, optional): Private key for signing

**Returns:** Transaction response dictionary

**Example:**
```python
reveal_response = sdk.reveal_result(
    validator_address="cosmos16tzn8wytv7srdw6v9l4q7ncmu8a092wrrfjp7l",
    task_id="task_001",
    result=result,  # Same as committed
    nonce=nonce     # Same as committed
)
```

### Query Methods

#### `get_task(task_id)`

Get task information by ID.

**Example:**
```python
task = sdk.get_task("task_001")
print(f"Status: {task['status']}")
```

#### `get_consensus_result(task_id)`

Get consensus result for a task.

**Example:**
```python
consensus = sdk.get_consensus_result("task_001")
print(f"Median: {consensus['median']}")
```

#### `get_all_tasks()`

Get all tasks.

**Example:**
```python
tasks = sdk.get_all_tasks()
for task in tasks:
    print(f"Task: {task['task_id']}")
```

#### `get_node_info()`

Get blockchain node information.

**Example:**
```python
info = sdk.get_node_info()
print(f"Chain: {info['default_node_info']['network']}")
```

#### `get_latest_block()`

Get the latest block information.

**Example:**
```python
block = sdk.get_latest_block()
print(f"Height: {block['block']['header']['height']}")
```

#### `get_supply(denom=None)`

Get token supply information.

**Example:**
```python
# Get all supply
supply = sdk.get_supply()

# Get specific denomination
stake_supply = sdk.get_supply(denom="stake")
```

## Examples

The SDK includes three comprehensive example scripts in the `examples/` directory:

### 1. Account Management ([account_management.py](examples/account_management.py))

Demonstrates:
- Querying node information
- Checking account details and balances
- Creating new accounts (with proper authorization)

**Run:**
```bash
cd sdk/python/examples
python account_management.py
```

### 2. Coin Management ([coin_management.py](examples/coin_management.py))

Demonstrates:
- Checking token balances
- Minting new coins to addresses
- Burning coins from module account
- Querying total supply

**Run:**
```bash
cd sdk/python/examples
python coin_management.py
```

### 3. Task Management ([task_management.py](examples/task_management.py))

Demonstrates:
- Creating inference tasks
- Commit-reveal consensus scheme
- Hash computation and verification
- Median calculation with outlier detection
- Querying task status and results

**Run:**
```bash
cd sdk/python/examples
python task_management.py
```

## Data Types

### `Coin`

Represents a coin amount with denomination.

**Attributes:**
- `denom` (str): Coin denomination (e.g., "stake", "token")
- `amount` (str): Amount as string (for large numbers)

**Example:**
```python
from median_sdk import Coin

coin = Coin(denom="stake", amount="1000000")
print(f"{coin.amount} {coin.denom}")
```

## Authorization and Signing

**Important Note:** The current SDK provides the structure for transactions but does not implement cryptographic signing. In production:

1. **Transaction Signing**: Implement proper transaction signing using Cosmos SDK signing libraries
2. **Private Keys**: Securely manage and use private keys for signing
3. **Authority Permissions**: Ensure the signer has proper authority for privileged operations (minting, burning, account creation)

### Required Authority

Certain operations require authority permissions:
- `create_account`: Requires creator to be the authority address
- `mint_coins`: Requires authority address
- `burn_coins`: Requires authority address

The default authority address is typically the governance module address:
```
cosmos10d07y265gmmuvt4z0w9aw880jnsr700j6zn9kn
```

## Architecture

### Commit-Reveal Consensus

The Median blockchain uses a commit-reveal scheme for inference tasks:

1. **Commit Phase**: Validators submit hashes of their results
   - Hash = SHA256(result + nonce)
   - This prevents copying other validators' results

2. **Reveal Phase**: Validators reveal actual results and nonces
   - Blockchain verifies: computed hash matches committed hash
   - Invalid reveals are rejected

3. **Consensus Calculation**:
   - Calculate median of all valid results
   - Set bounds: median ± 20%
   - Valid validators are within bounds
   - Invalid validators are outside bounds

**Example:**
```python
# Commit phase
result = 52000
nonce = 1234567
hash = sdk._compute_hash(result, nonce)
sdk.commit_result(validator, task_id, result, nonce)

# Reveal phase (after commit deadline)
sdk.reveal_result(validator, task_id, result, nonce)

# Consensus
# If median = 51750, bounds = [41400, 62100] (±20%)
# Result 52000 is within bounds → VALID
# Result 70000 is outside bounds → INVALID
```

## Error Handling

The SDK uses Python exceptions for error handling:

```python
try:
    balance = sdk.get_account_balance("cosmos1invalid...")
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
except Exception as e:
    print(f"Error: {e}")
```

## Configuration

### Environment Setup

The blockchain must be running and accessible:

```bash
# Default configuration
API URL: http://localhost:1317
RPC URL: http://localhost:26657
Chain ID: median
```

### Starting the Blockchain

```bash
cd /path/to/Median
./ignite chain serve
```

The blockchain will be available at:
- Blockchain API: http://0.0.0.0:1317
- Tendermint node: http://0.0.0.0:26657
- Token faucet: http://0.0.0.0:4500

## Development

### Project Structure

```
sdk/python/
├── median_sdk.py           # Main SDK module
├── README.md               # This file
└── examples/
    ├── account_management.py
    ├── coin_management.py
    └── task_management.py
```

### Testing

Run the example scripts to test SDK functionality:

```bash
# Ensure blockchain is running
cd sdk/python/examples

# Test account management
python account_management.py

# Test coin management
python coin_management.py

# Test task management
python task_management.py
```

## Troubleshooting

### Connection Errors

If you get connection errors:

1. **Check blockchain is running**:
   ```bash
   curl http://localhost:1317/cosmos/base/tendermint/v1beta1/node_info
   ```

2. **Verify API URL**: Ensure the API URL in your code matches the blockchain

3. **Check firewall**: Ensure port 1317 is accessible

### Transaction Failures

If transactions fail:

1. **Check authority**: Ensure you're using the correct authority address
2. **Verify signing**: Implement proper transaction signing
3. **Check account exists**: Query account before operations
4. **Review logs**: Check blockchain logs for detailed error messages

### Query Errors

If queries return unexpected results:

1. **Check endpoint**: Verify the API endpoint is correct
2. **Verify data exists**: Task/account may not exist yet
3. **Check response format**: API response structure may have changed

## Contributing

Contributions are welcome! Please ensure:

1. Code follows Python PEP 8 style guidelines
2. Add docstrings to new functions
3. Update README with new features
4. Test thoroughly with running blockchain

## License

This SDK is part of the Median blockchain project.

## Support

For issues and questions:
- GitHub Issues: [Median Repository](https://github.com/your-repo/median)
- Documentation: See `docs/` directory
- Examples: See `examples/` directory

## Changelog

### Version 1.0.0
- Initial release
- Account management APIs
- Coin minting and burning
- Task creation and consensus
- Query functionality
- Comprehensive examples

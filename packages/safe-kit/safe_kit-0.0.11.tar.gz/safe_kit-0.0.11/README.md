# Safe Kit (Python)

[![PyPI version](https://img.shields.io/pypi/v/safe-kit.svg)](https://pypi.org/project/safe-kit/)
[![Python versions](https://img.shields.io/pypi/pyversions/safe-kit.svg)](https://pypi.org/project/safe-kit/)
[![License](https://img.shields.io/pypi/l/safe-kit.svg)](https://github.com/smallyunet/safe-kit/blob/main/LICENSE)
[![CI](https://github.com/smallyunet/safe-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/smallyunet/safe-kit/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/smallyunet/safe-kit/branch/main/graph/badge.svg)](https://codecov.io/gh/smallyunet/safe-kit)

A Python implementation of the [Safe Protocol Kit](https://github.com/safe-global/safe-core-sdk), designed to mirror the developer experience of the official Node.js SDK.

## Features

- **DX First**: Intuitive API for interacting with Safe smart accounts.
- **Type Safe**: Built with Pydantic and fully typed for robust development.
- **Modern Stack**: Uses Web3.py, Eth-account, and Python 3.10+.
- **Full Protocol Support**: Supports Safe deployment, transaction creation, signing (EIP-712 & eth_sign), and execution.
- **Advanced Features**: MultiSend (batching), Safe Transaction Service integration, and more.

## Installation

You can install `safe-kit` via pip:

```bash
pip install safe-kit
```

Or with Poetry:

```bash
poetry add safe-kit
```

## Usage

### Initialization

```python
from web3 import Web3
from eth_account import Account
from safe_kit.safe import Safe
from safe_kit.adapter import Web3Adapter

# Setup Web3 and Signer
w3 = Web3(Web3.HTTPProvider("RPC_URL"))
owner = Account.from_key("PRIVATE_KEY")
adapter = Web3Adapter(web3=w3, signer=owner)

# Initialize Safe
safe = Safe(eth_adapter=adapter, safe_address="0xSafeAddress")
```

### Creating and Signing Transactions

```python
from safe_kit.types import SafeTransactionData

# Create a transaction (e.g., send ETH)
tx_data = SafeTransactionData(
    to="0xRecipient",
    value=1000000000000000000, # 1 ETH
    data="0x"
)

safe_tx = safe.create_transaction(tx_data)

# Sign the transaction
# Supports "eth_sign_typed_data" (default, EIP-712) or "eth_sign" (legacy)
signed_tx = safe.sign_transaction(safe_tx)
```

### Executing Transactions

```python
# Execute the transaction on-chain
tx_hash = safe.execute_transaction(signed_tx)
print(f"Transaction executed: {tx_hash}")
```

For more advanced usage (Batching, Transaction Service, Deployment), please refer to the [User Guide](https://smallyunet.github.io/safe-kit/user_guide/).

## Development

### Setup

```bash
# Install dependencies
poetry install
```

### Running Tests

```bash
poetry run pytest
```

### Linting

```bash
poetry run ruff check .
poetry run mypy .
```

## Roadmap

See [docs/roadmap.md](docs/roadmap.md) for the current implementation status.

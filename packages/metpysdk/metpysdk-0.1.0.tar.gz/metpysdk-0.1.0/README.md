# metpysdk

**metpysdk** is a Python SDK for interacting with **Meteora DLMM (Dynamic Liquidity Market Maker)** on Solana.

It provides high-level, async-friendly primitives for:
- querying DLMM pairs
- inspecting bins and liquidity
- reading positions and rewards
- parsing on-chain accounts safely and accurately

The SDK is designed as a **library**, not a script:
- clean public API
- explicit versioning
- byte-accurate account parsing
- minimal, modern dependency set

> ⚠️ This project is in active development (`0.x`).  
> APIs may change until `1.0.0`.

---

## Features

- 🚀 Async-first API (`asyncio`)
- 🔍 Accurate parsing of DLMM on-chain accounts
- 🧱 Construct-based binary layouts (no abandoned deps)
- 🧠 Clear separation between public API and internals
- 🛠️ Designed for bots, analytics, and backend services

---

## Installation

### Requirements
- Python **3.9+**
- Poetry (recommended) or pip

### With Poetry (recommended)

```bash
poetry add metpysdk
```
### With pip
```bash
pip install metpysdk
```
### Quick Example
```python
import asyncio

from metpysdk import DLMMClient
from solders.pubkey import Pubkey


async def main():
    client = DLMMClient()

    lb_pair = Pubkey.from_string(
        "INSERT_LB_PAIR_ADDRESS_HERE"
    )

    active_bin = await client.get_active_bin(lb_pair)

    print("Active bin ID:", active_bin.bin_id)
    print("Price:", active_bin.price)


asyncio.run(main())
```
### Project Structure
```text
metpysdk/
├── accounts/     # Parsed on-chain account models
├── dlmm/         # Core DLMM client logic
├── helpers/      # High-level helpers and combinators
├── layouts/      # Binary layouts (construct-based)
├── utils/        # RPC, filters, derivations, constants
└── __init__.py   # Public API surface
```
Only symbols re-exported from package-level modules are considered public API.\
Everything else may change without notice until 1.0.0.

### Public API
The main entry point is:

```python
from metpysdk import DLMMClient
```
Additional data models and enums are exposed via:

```python

from metpysdk.accounts import (
    Position,
    ActiveBin,
    StrategyParameters,
)
```
Deep imports from internal modules are not supported.

### Development
Setup
```bash
git clone https://github.com/yourname/metpysdk.git
cd metpysdk
poetry install
```
Poetry will create a local .venv/ automatically.

### Linting

```
poetry run ruff check src/metpysdk
poetry run pylint src/metpysdk
```
### Tests
```
poetry run pytest
```
### Versioning
This project follows semantic versioning:
```
0.x.y — unstable, breaking changes allowed
1.0.0 — first stable API
>=1.0.0 — no breaking changes without major bump
```
### License
MIT License © 2025 Ivan Bezborodov

See LICENSE for details.

### Disclaimer
This SDK is provided as-is, without warranties.\
Interacting with on-chain programs involves financial risk.\
Always validate results independently before using in production.
---

# merkle-tree

Merkle tree and hash chain utilities for immutable audit logs.

## Features

- **Hash Chaining**: Link records together with SHA-256 hashes to create tamper-evident chains
- **Merkle Trees**: Compute Merkle roots for efficient batch verification
- **Batch Processing**: Process multiple records as a batch with automatic sequencing
- **Chain Verification**: Detect tampering by verifying hash chain integrity
- **Protocol-Based**: Flexible design using Python protocols for easy integration

## Installation

```bash
pip install lokryn-merkle-tree
```

Or with uv:

```bash
uv add lokryn-merkle-tree
```

## Quick Start

### 1. Define Your Record Type

Any class can be hashed as long as it implements the `HashableRecord` protocol. You control exactly what data is included in the hash by implementing `get_hash_content()`:

```python
from dataclasses import dataclass
from merkle_tree import HashableRecord, Hasher


@dataclass
class AuditEntry:
    """An audit log entry."""

    timestamp: str
    user_id: str
    action: str
    details: str

    # Required protocol fields
    record_hash: str = ""
    prev_hash: str = ""
    batch_id: str = ""
    batch_sequence: int = 0
    batch_merkle_root: str = ""

    def get_hash_content(self) -> bytes:
        """Define what data is included in the hash."""
        return f"{self.timestamp}|{self.user_id}|{self.action}|{self.details}".encode()
```

### 2. Hash Individual Records

```python
hasher = Hasher()

entry1 = AuditEntry(
    timestamp="2024-01-15T10:30:00Z",
    user_id="user_123",
    action="LOGIN",
    details="Successful login from 192.168.1.1"
)

entry2 = AuditEntry(
    timestamp="2024-01-15T10:31:00Z",
    user_id="user_123",
    action="VIEW",
    details="Viewed document doc_456"
)

hasher.hash_record(entry1)
hasher.hash_record(entry2)

# Records are now chained
print(entry1.record_hash)  # SHA-256 hash of entry1
print(entry2.prev_hash)    # Points to entry1's hash
```

### 3. Process Batches with Merkle Roots

```python
hasher = Hasher()

entries = [
    AuditEntry(timestamp="2024-01-15T10:30:00Z", user_id="user_1", action="CREATE", details="..."),
    AuditEntry(timestamp="2024-01-15T10:30:01Z", user_id="user_2", action="UPDATE", details="..."),
    AuditEntry(timestamp="2024-01-15T10:30:02Z", user_id="user_1", action="DELETE", details="..."),
]

merkle_root = hasher.hash_batch(entries)

# All entries share the same batch_id
# The last entry contains the merkle_root
print(entries[-1].batch_merkle_root)
```

### 4. Verify Integrity

```python
# Verify hash chain continuity
is_valid, breaks = Hasher.verify_chain(entries)
if not is_valid:
    print(f"Chain broken at indices: {[b['record_index'] for b in breaks]}")

# Verify batch Merkle root
is_valid, stored_root, computed_root = Hasher.verify_batch(entries)
if not is_valid:
    print(f"Merkle root mismatch: stored={stored_root}, computed={computed_root}")
```

## API Reference

### `HashableRecord` Protocol

A protocol defining the interface for hashable records:

| Attribute | Type | Description |
|-----------|------|-------------|
| `record_hash` | `str` | SHA-256 hash of this record's content |
| `prev_hash` | `str` | Hash of the previous record in the chain |
| `batch_id` | `str` | UUID identifying the batch this record belongs to |
| `batch_sequence` | `int` | Zero-indexed position within the batch |
| `batch_merkle_root` | `str` | Merkle root (set only on the last record of a batch) |

| Method | Returns | Description |
|--------|---------|-------------|
| `get_hash_content()` | `bytes` | The bytes to be hashed for this record |

### `Hasher` Class

#### Constructor

```python
Hasher(last_hash: str = "")
```

Create a new hasher. Optionally provide the last hash from an existing chain to continue it.

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `last_hash` | `str` | The hash of the most recently processed record |

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `set_last_hash(last_hash: str)` | `None` | Update the chain state |
| `hash_record(record: T)` | `str` | Hash a record and link it to the chain |
| `hash_batch(records: list[T])` | `str` | Hash a batch and compute Merkle root |
| `compute_merkle_root(hashes: list[str])` | `str` | Static: compute Merkle root from hashes |
| `verify_chain(records: list[T])` | `tuple[bool, list[dict]]` | Static: verify chain continuity |
| `verify_batch(records: list[T])` | `tuple[bool, str, str]` | Static: verify batch Merkle root |

## Flexible Record Types

The protocol-based design means you can hash any data structure. Here are a few examples:

```python
# A simple log entry
@dataclass
class LogEntry:
    message: str
    level: str
    # ... protocol fields ...

    def get_hash_content(self) -> bytes:
        return f"{self.level}:{self.message}".encode()


# A financial transaction
@dataclass
class Transaction:
    from_account: str
    to_account: str
    amount: Decimal
    currency: str
    # ... protocol fields ...

    def get_hash_content(self) -> bytes:
        return f"{self.from_account}>{self.to_account}:{self.amount}{self.currency}".encode()


# A file with binary content
@dataclass
class FileRecord:
    filename: str
    content: bytes
    # ... protocol fields ...

    def get_hash_content(self) -> bytes:
        return self.filename.encode() + self.content
```

The `get_hash_content()` method gives you full control over what data contributes to the hash. Include fields that should be immutable; exclude fields that may change (like status or metadata).

## How It Works

### Hash Chaining

Each record's `prev_hash` points to the previous record's `record_hash`, forming a chain:

```
Record 1          Record 2          Record 3
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│ record_hash │◄──│ prev_hash   │   │             │
│     A       │   │     A       │◄──│ prev_hash   │
│             │   │ record_hash │   │     B       │
│ prev_hash   │   │     B       │   │ record_hash │
│     A*      │   │             │   │     C       │
└─────────────┘   └─────────────┘   └─────────────┘

* First record: prev_hash = record_hash
```

### Merkle Tree

Batch processing computes a Merkle root for efficient verification:

```
                    Root
                   /    \
                  /      \
               H(AB)    H(CD)
               /  \      /  \
              A    B    C    D

A, B, C, D = record hashes
H(AB) = SHA-256(A + B)
Root = SHA-256(H(AB) + H(CD))
```

For odd numbers of hashes, the last hash is carried up unchanged.

## Continuing an Existing Chain

To append to an existing chain, initialize `Hasher` with the last known hash:

```python
# Get the last hash from your database
last_hash = db.get_last_record_hash()

# Continue the chain
hasher = Hasher(last_hash=last_hash)
hasher.hash_record(new_entry)  # Links to existing chain
```

## Use Cases

- **Audit Logs**: Create tamper-evident logs for compliance and security
- **Data Integrity**: Verify that historical data hasn't been modified
- **Blockchain-like Structures**: Build lightweight chain structures without full blockchain overhead
- **Document Versioning**: Track document changes with cryptographic proof
- **Event Sourcing**: Ensure event stream integrity

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/lokryn-llc/merkle-tree.git
cd merkle-tree

# Install dependencies with uv
uv sync
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run only unit tests
uv run pytest tests/test_hasher.py

# Run only integration tests
uv run pytest tests/test_integration.py
```

### Linting

```bash
uv run ruff check .
uv run ruff format .
```

## License

This project is licensed under the GNU Affero General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

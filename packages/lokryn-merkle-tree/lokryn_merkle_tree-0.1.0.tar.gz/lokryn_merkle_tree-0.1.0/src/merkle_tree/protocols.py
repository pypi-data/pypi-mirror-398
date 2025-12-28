"""Protocol definitions for hashable records."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class HashableRecord(Protocol):
    """Protocol for records that can be hashed and chained."""

    record_hash: str
    prev_hash: str
    batch_id: str
    batch_sequence: int
    batch_merkle_root: str

    def get_hash_content(self) -> bytes:
        """Return the bytes to hash for this record."""
        ...

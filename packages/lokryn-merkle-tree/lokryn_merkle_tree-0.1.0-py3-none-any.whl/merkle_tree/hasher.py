"""SHA256 hashing, Merkle tree computation, and hash chain management."""

import hashlib
import uuid
from typing import TypeVar

from .protocols import HashableRecord

T = TypeVar("T", bound=HashableRecord)


class Hasher:
    """Manages record hashing, hash chains, and Merkle tree computation."""

    def __init__(self, last_hash: str = "") -> None:
        self._last_hash: str = last_hash
        self._is_first_record: bool = last_hash == ""

    @property
    def last_hash(self) -> str:
        return self._last_hash

    def set_last_hash(self, last_hash: str) -> None:
        self._last_hash = last_hash
        self._is_first_record = last_hash == ""

    def hash_record(self, record: T) -> str:
        """Hash a record and link it to the chain."""
        content = record.get_hash_content()
        record_hash = hashlib.sha256(content).hexdigest()
        record.record_hash = record_hash

        if self._is_first_record:
            record.prev_hash = record_hash
            self._is_first_record = False
        else:
            record.prev_hash = self._last_hash

        self._last_hash = record_hash
        return record_hash

    def hash_batch(self, records: list[T]) -> str:
        """Hash a batch and compute Merkle root."""
        if not records:
            return ""

        batch_id = str(uuid.uuid4())
        hashes: list[str] = []

        for i, record in enumerate(records):
            record.batch_id = batch_id
            record.batch_sequence = i
            hashes.append(self.hash_record(record))

        merkle_root = self.compute_merkle_root(hashes)
        records[-1].batch_merkle_root = merkle_root
        return merkle_root

    @staticmethod
    def compute_merkle_root(hashes: list[str]) -> str:
        """Compute Merkle root from a list of hashes."""
        if not hashes:
            return ""
        if len(hashes) == 1:
            return hashes[0]

        current_level = list(hashes)
        while len(current_level) > 1:
            next_level: list[str] = []
            for i in range(0, len(current_level), 2):
                if i + 1 < len(current_level):
                    combined = current_level[i] + current_level[i + 1]
                    next_level.append(hashlib.sha256(combined.encode()).hexdigest())
                else:
                    next_level.append(current_level[i])
            current_level = next_level
        return current_level[0]

    @staticmethod
    def verify_chain(records: list[T]) -> tuple[bool, list[dict]]:
        """Verify hash chain continuity."""
        if not records:
            return True, []

        breaks: list[dict] = []
        for i, record in enumerate(records):
            if i == 0:
                if record.prev_hash != record.record_hash:
                    breaks.append(
                        {
                            "record_index": i,
                            "expected_prev_hash": record.record_hash,
                            "actual_prev_hash": record.prev_hash,
                        }
                    )
            else:
                expected = records[i - 1].record_hash
                if record.prev_hash != expected:
                    breaks.append(
                        {
                            "record_index": i,
                            "expected_prev_hash": expected,
                            "actual_prev_hash": record.prev_hash,
                        }
                    )
        return len(breaks) == 0, breaks

    @staticmethod
    def verify_batch(records: list[T]) -> tuple[bool, str, str]:
        """Verify batch Merkle root."""
        if not records:
            return True, "", ""

        stored_root = ""
        for record in reversed(records):
            if record.batch_merkle_root:
                stored_root = record.batch_merkle_root
                break

        hashes = [r.record_hash for r in records]
        computed_root = Hasher.compute_merkle_root(hashes)
        return stored_root == computed_root, stored_root, computed_root

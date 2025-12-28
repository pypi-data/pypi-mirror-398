"""Pytest fixtures and test utilities for merkle-tree tests."""

from dataclasses import dataclass

import pytest

from merkle_tree import Hasher


@dataclass
class SampleRecord:
    """A sample record implementing the HashableRecord protocol."""

    data: str
    record_hash: str = ""
    prev_hash: str = ""
    batch_id: str = ""
    batch_sequence: int = 0
    batch_merkle_root: str = ""

    def get_hash_content(self) -> bytes:
        """Return the bytes to hash for this record."""
        return self.data.encode("utf-8")


@dataclass
class ComplexRecord:
    """A more complex record with multiple fields for hashing."""

    id: int
    name: str
    value: float
    record_hash: str = ""
    prev_hash: str = ""
    batch_id: str = ""
    batch_sequence: int = 0
    batch_merkle_root: str = ""

    def get_hash_content(self) -> bytes:
        """Return the bytes to hash for this record."""
        return f"{self.id}:{self.name}:{self.value}".encode()


@pytest.fixture
def hasher() -> Hasher:
    """Return a fresh Hasher instance."""
    return Hasher()


@pytest.fixture
def hasher_with_history() -> Hasher:
    """Return a Hasher with an existing chain."""
    return Hasher(last_hash="abc123def456")


@pytest.fixture
def sample_record() -> SampleRecord:
    """Return a single sample record."""
    return SampleRecord(data="test data")


@pytest.fixture
def sample_records() -> list[SampleRecord]:
    """Return a list of sample records for batch testing."""
    return [
        SampleRecord(data="record 1"),
        SampleRecord(data="record 2"),
        SampleRecord(data="record 3"),
    ]


@pytest.fixture
def complex_records() -> list[ComplexRecord]:
    """Return a list of complex records for batch testing."""
    return [
        ComplexRecord(id=1, name="alpha", value=1.5),
        ComplexRecord(id=2, name="beta", value=2.5),
        ComplexRecord(id=3, name="gamma", value=3.5),
        ComplexRecord(id=4, name="delta", value=4.5),
    ]

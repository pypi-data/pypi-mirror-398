"""Tests for the Hasher class and hash chain functionality."""

import hashlib

from merkle_tree import HashableRecord, Hasher

from .conftest import ComplexRecord, SampleRecord


class TestHashableRecordProtocol:
    """Tests for the HashableRecord protocol."""

    def test_sample_record_implements_protocol(self, sample_record: SampleRecord) -> None:
        """Verify SampleRecord implements HashableRecord protocol."""
        assert isinstance(sample_record, HashableRecord)

    def test_complex_record_implements_protocol(self) -> None:
        """Verify ComplexRecord implements HashableRecord protocol."""
        record = ComplexRecord(id=1, name="test", value=1.0)
        assert isinstance(record, HashableRecord)

    def test_protocol_has_required_attributes(self, sample_record: SampleRecord) -> None:
        """Verify all required protocol attributes exist."""
        assert hasattr(sample_record, "record_hash")
        assert hasattr(sample_record, "prev_hash")
        assert hasattr(sample_record, "batch_id")
        assert hasattr(sample_record, "batch_sequence")
        assert hasattr(sample_record, "batch_merkle_root")
        assert hasattr(sample_record, "get_hash_content")

    def test_get_hash_content_returns_bytes(self, sample_record: SampleRecord) -> None:
        """Verify get_hash_content returns bytes."""
        content = sample_record.get_hash_content()
        assert isinstance(content, bytes)


class TestHasherInitialization:
    """Tests for Hasher initialization and state management."""

    def test_default_initialization(self, hasher: Hasher) -> None:
        """Hasher initializes with empty last_hash."""
        assert hasher.last_hash == ""

    def test_initialization_with_last_hash(self, hasher_with_history: Hasher) -> None:
        """Hasher can be initialized with existing chain hash."""
        assert hasher_with_history.last_hash == "abc123def456"

    def test_set_last_hash(self, hasher: Hasher) -> None:
        """set_last_hash updates the chain state."""
        hasher.set_last_hash("new_hash_value")
        assert hasher.last_hash == "new_hash_value"

    def test_set_last_hash_empty_resets_first_record_flag(self, hasher: Hasher) -> None:
        """Setting empty last_hash resets to first record behavior."""
        hasher.set_last_hash("some_hash")
        hasher.set_last_hash("")
        record = SampleRecord(data="test")
        hasher.hash_record(record)
        assert record.prev_hash == record.record_hash


class TestHashRecord:
    """Tests for the hash_record method."""

    def test_hash_record_returns_hash(self, hasher: Hasher, sample_record: SampleRecord) -> None:
        """hash_record returns a SHA256 hash string."""
        result = hasher.hash_record(sample_record)
        assert isinstance(result, str)
        assert len(result) == 64  # SHA256 hex length

    def test_hash_record_sets_record_hash(
        self, hasher: Hasher, sample_record: SampleRecord
    ) -> None:
        """hash_record sets the record_hash attribute."""
        result = hasher.hash_record(sample_record)
        assert sample_record.record_hash == result

    def test_hash_record_computes_correct_hash(
        self, hasher: Hasher, sample_record: SampleRecord
    ) -> None:
        """hash_record computes the correct SHA256 hash."""
        expected = hashlib.sha256(sample_record.get_hash_content()).hexdigest()
        result = hasher.hash_record(sample_record)
        assert result == expected

    def test_first_record_prev_hash_equals_record_hash(
        self, hasher: Hasher, sample_record: SampleRecord
    ) -> None:
        """First record's prev_hash should equal its record_hash."""
        hasher.hash_record(sample_record)
        assert sample_record.prev_hash == sample_record.record_hash

    def test_second_record_links_to_first(self, hasher: Hasher) -> None:
        """Second record's prev_hash should be first record's hash."""
        record1 = SampleRecord(data="first")
        record2 = SampleRecord(data="second")

        hash1 = hasher.hash_record(record1)
        hasher.hash_record(record2)

        assert record2.prev_hash == hash1

    def test_chain_continuity(self, hasher: Hasher) -> None:
        """Multiple records form a proper chain."""
        records = [SampleRecord(data=f"record {i}") for i in range(5)]
        for record in records:
            hasher.hash_record(record)

        for i in range(1, len(records)):
            assert records[i].prev_hash == records[i - 1].record_hash

    def test_hasher_with_history_links_correctly(self, hasher_with_history: Hasher) -> None:
        """Record links to existing chain when hasher has history."""
        record = SampleRecord(data="new record")
        hasher_with_history.hash_record(record)
        assert record.prev_hash == "abc123def456"

    def test_last_hash_updates_after_hashing(
        self, hasher: Hasher, sample_record: SampleRecord
    ) -> None:
        """last_hash property updates after hashing a record."""
        result = hasher.hash_record(sample_record)
        assert hasher.last_hash == result

    def test_deterministic_hashing(self) -> None:
        """Same data produces same hash."""
        hasher1 = Hasher()
        hasher2 = Hasher()
        record1 = SampleRecord(data="identical")
        record2 = SampleRecord(data="identical")

        hash1 = hasher1.hash_record(record1)
        hash2 = hasher2.hash_record(record2)

        assert hash1 == hash2

    def test_different_data_produces_different_hash(self, hasher: Hasher) -> None:
        """Different data produces different hashes."""
        record1 = SampleRecord(data="data1")
        record2 = SampleRecord(data="data2")

        hash1 = hasher.hash_record(record1)
        hasher.set_last_hash("")
        hash2 = hasher.hash_record(record2)

        assert hash1 != hash2


class TestHashBatch:
    """Tests for the hash_batch method."""

    def test_hash_batch_returns_merkle_root(
        self, hasher: Hasher, sample_records: list[SampleRecord]
    ) -> None:
        """hash_batch returns a merkle root string."""
        result = hasher.hash_batch(sample_records)
        assert isinstance(result, str)
        assert len(result) == 64

    def test_hash_batch_empty_list(self, hasher: Hasher) -> None:
        """hash_batch with empty list returns empty string."""
        result = hasher.hash_batch([])
        assert result == ""

    def test_hash_batch_sets_batch_id(
        self, hasher: Hasher, sample_records: list[SampleRecord]
    ) -> None:
        """hash_batch sets the same batch_id for all records."""
        hasher.hash_batch(sample_records)
        batch_ids = {r.batch_id for r in sample_records}
        assert len(batch_ids) == 1
        assert batch_ids.pop() != ""

    def test_hash_batch_sets_sequence(
        self, hasher: Hasher, sample_records: list[SampleRecord]
    ) -> None:
        """hash_batch sets sequential batch_sequence values."""
        hasher.hash_batch(sample_records)
        for i, record in enumerate(sample_records):
            assert record.batch_sequence == i

    def test_hash_batch_sets_merkle_root_on_last_record(
        self, hasher: Hasher, sample_records: list[SampleRecord]
    ) -> None:
        """hash_batch sets merkle_root only on the last record."""
        merkle_root = hasher.hash_batch(sample_records)
        for record in sample_records[:-1]:
            assert record.batch_merkle_root == ""
        assert sample_records[-1].batch_merkle_root == merkle_root

    def test_hash_batch_hashes_all_records(
        self, hasher: Hasher, sample_records: list[SampleRecord]
    ) -> None:
        """hash_batch computes hash for all records."""
        hasher.hash_batch(sample_records)
        for record in sample_records:
            assert record.record_hash != ""
            assert len(record.record_hash) == 64

    def test_hash_batch_maintains_chain(
        self, hasher: Hasher, sample_records: list[SampleRecord]
    ) -> None:
        """hash_batch maintains proper hash chain within batch."""
        hasher.hash_batch(sample_records)
        for i in range(1, len(sample_records)):
            assert sample_records[i].prev_hash == sample_records[i - 1].record_hash

    def test_multiple_batches_chain_correctly(self, hasher: Hasher) -> None:
        """Multiple batches chain together correctly."""
        batch1 = [SampleRecord(data=f"batch1_{i}") for i in range(3)]
        batch2 = [SampleRecord(data=f"batch2_{i}") for i in range(3)]

        hasher.hash_batch(batch1)
        hasher.hash_batch(batch2)

        assert batch2[0].prev_hash == batch1[-1].record_hash

    def test_single_record_batch(self, hasher: Hasher) -> None:
        """hash_batch works with a single record."""
        records = [SampleRecord(data="only one")]
        merkle_root = hasher.hash_batch(records)
        assert merkle_root == records[0].record_hash
        assert records[0].batch_merkle_root == merkle_root


class TestComputeMerkleRoot:
    """Tests for the compute_merkle_root static method."""

    def test_empty_list(self) -> None:
        """Empty list returns empty string."""
        assert Hasher.compute_merkle_root([]) == ""

    def test_single_hash(self) -> None:
        """Single hash returns itself as root."""
        hash_val = "abc123"
        assert Hasher.compute_merkle_root([hash_val]) == hash_val

    def test_two_hashes(self) -> None:
        """Two hashes are combined correctly."""
        h1 = "a" * 64
        h2 = "b" * 64
        expected = hashlib.sha256((h1 + h2).encode()).hexdigest()
        assert Hasher.compute_merkle_root([h1, h2]) == expected

    def test_power_of_two_hashes(self) -> None:
        """Power of two hashes builds balanced tree."""
        hashes = [f"{i:064x}" for i in range(4)]
        result = Hasher.compute_merkle_root(hashes)
        assert isinstance(result, str)
        assert len(result) == 64

    def test_odd_number_of_hashes(self) -> None:
        """Odd number of hashes handles unpaired node."""
        hashes = ["a" * 64, "b" * 64, "c" * 64]
        result = Hasher.compute_merkle_root(hashes)
        assert isinstance(result, str)
        assert len(result) == 64

    def test_deterministic_result(self) -> None:
        """Same input produces same merkle root."""
        hashes = ["abc", "def", "ghi"]
        result1 = Hasher.compute_merkle_root(hashes.copy())
        result2 = Hasher.compute_merkle_root(hashes.copy())
        assert result1 == result2

    def test_order_matters(self) -> None:
        """Different order produces different root."""
        hashes = ["abc", "def", "ghi"]
        result1 = Hasher.compute_merkle_root(hashes)
        result2 = Hasher.compute_merkle_root(list(reversed(hashes)))
        assert result1 != result2

    def test_manual_computation_two_level_tree(self) -> None:
        """Verify merkle computation with known values."""
        h1 = hashlib.sha256(b"leaf1").hexdigest()
        h2 = hashlib.sha256(b"leaf2").hexdigest()
        h3 = hashlib.sha256(b"leaf3").hexdigest()
        h4 = hashlib.sha256(b"leaf4").hexdigest()

        level1_left = hashlib.sha256((h1 + h2).encode()).hexdigest()
        level1_right = hashlib.sha256((h3 + h4).encode()).hexdigest()
        expected_root = hashlib.sha256((level1_left + level1_right).encode()).hexdigest()

        result = Hasher.compute_merkle_root([h1, h2, h3, h4])
        assert result == expected_root


class TestVerifyChain:
    """Tests for the verify_chain static method."""

    def test_empty_list(self) -> None:
        """Empty list is valid."""
        valid, breaks = Hasher.verify_chain([])
        assert valid is True
        assert breaks == []

    def test_valid_single_record_chain(self, hasher: Hasher) -> None:
        """Single properly hashed record is valid."""
        record = SampleRecord(data="single")
        hasher.hash_record(record)
        valid, breaks = Hasher.verify_chain([record])
        assert valid is True
        assert breaks == []

    def test_valid_multi_record_chain(
        self, hasher: Hasher, sample_records: list[SampleRecord]
    ) -> None:
        """Properly chained records are valid."""
        for record in sample_records:
            hasher.hash_record(record)
        valid, breaks = Hasher.verify_chain(sample_records)
        assert valid is True
        assert breaks == []

    def test_broken_first_record(self) -> None:
        """First record with mismatched prev_hash is invalid."""
        record = SampleRecord(data="test")
        record.record_hash = "abc123"
        record.prev_hash = "different"
        valid, breaks = Hasher.verify_chain([record])
        assert valid is False
        assert len(breaks) == 1
        assert breaks[0]["record_index"] == 0

    def test_broken_chain_middle(self, hasher: Hasher) -> None:
        """Broken chain in middle is detected."""
        records = [SampleRecord(data=f"record {i}") for i in range(5)]
        for record in records:
            hasher.hash_record(record)

        records[2].prev_hash = "tampered_hash"
        valid, breaks = Hasher.verify_chain(records)
        assert valid is False
        assert len(breaks) == 1
        assert breaks[0]["record_index"] == 2
        assert breaks[0]["expected_prev_hash"] == records[1].record_hash
        assert breaks[0]["actual_prev_hash"] == "tampered_hash"

    def test_multiple_breaks(self, hasher: Hasher) -> None:
        """Multiple chain breaks are all detected."""
        records = [SampleRecord(data=f"record {i}") for i in range(5)]
        for record in records:
            hasher.hash_record(record)

        records[1].prev_hash = "tampered1"
        records[3].prev_hash = "tampered2"

        valid, breaks = Hasher.verify_chain(records)
        assert valid is False
        assert len(breaks) == 2
        assert breaks[0]["record_index"] == 1
        assert breaks[1]["record_index"] == 3

    def test_verify_chain_with_batch(
        self, hasher: Hasher, sample_records: list[SampleRecord]
    ) -> None:
        """Batch-hashed records maintain valid chain."""
        hasher.hash_batch(sample_records)
        valid, breaks = Hasher.verify_chain(sample_records)
        assert valid is True
        assert breaks == []


class TestVerifyBatch:
    """Tests for the verify_batch static method."""

    def test_empty_list(self) -> None:
        """Empty list is valid with empty roots."""
        valid, stored, computed = Hasher.verify_batch([])
        assert valid is True
        assert stored == ""
        assert computed == ""

    def test_valid_batch(self, hasher: Hasher, sample_records: list[SampleRecord]) -> None:
        """Properly hashed batch is valid."""
        hasher.hash_batch(sample_records)
        valid, stored, computed = Hasher.verify_batch(sample_records)
        assert valid is True
        assert stored == computed
        assert stored != ""

    def test_tampered_record_hash_invalidates_batch(
        self, hasher: Hasher, sample_records: list[SampleRecord]
    ) -> None:
        """Modifying a record hash invalidates the batch."""
        hasher.hash_batch(sample_records)
        sample_records[1].record_hash = "tampered_hash"
        valid, stored, computed = Hasher.verify_batch(sample_records)
        assert valid is False
        assert stored != computed

    def test_tampered_merkle_root_invalidates_batch(
        self, hasher: Hasher, sample_records: list[SampleRecord]
    ) -> None:
        """Modifying the merkle root invalidates the batch."""
        hasher.hash_batch(sample_records)
        sample_records[-1].batch_merkle_root = "tampered_root"
        valid, stored, computed = Hasher.verify_batch(sample_records)
        assert valid is False

    def test_verify_batch_finds_merkle_root_from_end(self, hasher: Hasher) -> None:
        """verify_batch searches for merkle root from end of list."""
        records = [SampleRecord(data=f"record {i}") for i in range(5)]
        hasher.hash_batch(records)
        valid, stored, computed = Hasher.verify_batch(records)
        assert valid is True
        assert stored == records[-1].batch_merkle_root

    def test_single_record_batch_valid(self, hasher: Hasher) -> None:
        """Single record batch is valid."""
        records = [SampleRecord(data="only")]
        hasher.hash_batch(records)
        valid, stored, computed = Hasher.verify_batch(records)
        assert valid is True
        assert stored == computed


class TestComplexRecords:
    """Tests using ComplexRecord to verify protocol flexibility."""

    def test_complex_record_hashing(
        self, hasher: Hasher, complex_records: list[ComplexRecord]
    ) -> None:
        """ComplexRecord works correctly with Hasher."""
        hasher.hash_batch(complex_records)
        valid, breaks = Hasher.verify_chain(complex_records)
        assert valid is True

    def test_complex_record_merkle_verification(
        self, hasher: Hasher, complex_records: list[ComplexRecord]
    ) -> None:
        """ComplexRecord batch verification works correctly."""
        hasher.hash_batch(complex_records)
        valid, stored, computed = Hasher.verify_batch(complex_records)
        assert valid is True

    def test_complex_record_content_affects_hash(self, hasher: Hasher) -> None:
        """Different ComplexRecord content produces different hashes."""
        record1 = ComplexRecord(id=1, name="test", value=1.0)
        record2 = ComplexRecord(id=1, name="test", value=2.0)

        hash1 = hasher.hash_record(record1)
        hasher.set_last_hash("")
        hash2 = hasher.hash_record(record2)

        assert hash1 != hash2


class TestEdgeCases:
    """Edge case tests for robustness."""

    def test_unicode_data(self, hasher: Hasher) -> None:
        """Unicode data is handled correctly."""
        record = SampleRecord(data="Hello 世界 🌍")
        result = hasher.hash_record(record)
        assert len(result) == 64

    def test_empty_data(self, hasher: Hasher) -> None:
        """Empty data is handled correctly."""
        record = SampleRecord(data="")
        result = hasher.hash_record(record)
        expected = hashlib.sha256(b"").hexdigest()
        assert result == expected

    def test_large_batch(self, hasher: Hasher) -> None:
        """Large batch is handled correctly."""
        records = [SampleRecord(data=f"record {i}") for i in range(100)]
        merkle_root = hasher.hash_batch(records)
        assert len(merkle_root) == 64
        valid, breaks = Hasher.verify_chain(records)
        assert valid is True

    def test_very_long_data(self, hasher: Hasher) -> None:
        """Very long data is handled correctly."""
        long_data = "x" * 100000
        record = SampleRecord(data=long_data)
        result = hasher.hash_record(record)
        assert len(result) == 64

    def test_special_characters_in_data(self, hasher: Hasher) -> None:
        """Special characters are handled correctly."""
        record = SampleRecord(data="line1\nline2\ttab\r\nwindows")
        result = hasher.hash_record(record)
        assert len(result) == 64

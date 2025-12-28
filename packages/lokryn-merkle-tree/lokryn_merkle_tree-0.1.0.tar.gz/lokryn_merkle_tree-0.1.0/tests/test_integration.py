"""End-to-end integration tests for merkle-tree."""

from dataclasses import dataclass
from decimal import Decimal

from merkle_tree import Hasher


@dataclass
class AuditEntry:
    """Simulates a real audit log entry."""

    timestamp: str
    user_id: str
    action: str
    resource: str
    details: str
    record_hash: str = ""
    prev_hash: str = ""
    batch_id: str = ""
    batch_sequence: int = 0
    batch_merkle_root: str = ""

    def get_hash_content(self) -> bytes:
        content = f"{self.timestamp}|{self.user_id}|{self.action}|{self.resource}|{self.details}"
        return content.encode()


@dataclass
class Transaction:
    """Simulates a financial transaction."""

    tx_id: str
    from_account: str
    to_account: str
    amount: Decimal
    currency: str
    timestamp: str
    record_hash: str = ""
    prev_hash: str = ""
    batch_id: str = ""
    batch_sequence: int = 0
    batch_merkle_root: str = ""

    def get_hash_content(self) -> bytes:
        parts = [self.tx_id, self.from_account, self.to_account]
        parts.extend([str(self.amount), self.currency, self.timestamp])
        return "|".join(parts).encode()


class TestAuditLogWorkflow:
    """End-to-end test simulating an audit log system."""

    def test_complete_audit_workflow(self) -> None:
        """Simulate a complete audit log workflow with multiple sessions."""
        # Session 1: Initial batch of audit entries
        hasher = Hasher()

        batch1 = [
            AuditEntry(
                timestamp="2024-01-15T09:00:00Z",
                user_id="admin",
                action="LOGIN",
                resource="system",
                details="Admin logged in",
            ),
            AuditEntry(
                timestamp="2024-01-15T09:01:00Z",
                user_id="admin",
                action="CREATE",
                resource="user:john",
                details="Created user account",
            ),
            AuditEntry(
                timestamp="2024-01-15T09:02:00Z",
                user_id="admin",
                action="GRANT",
                resource="user:john",
                details="Granted read permissions",
            ),
        ]

        hasher.hash_batch(batch1)
        last_hash_session_1 = hasher.last_hash

        # Verify batch 1 integrity
        chain_valid, breaks = Hasher.verify_chain(batch1)
        assert chain_valid, f"Batch 1 chain invalid: {breaks}"

        batch_valid, stored, computed = Hasher.verify_batch(batch1)
        assert batch_valid, f"Batch 1 merkle mismatch: {stored} != {computed}"

        # Session 2: Continue the chain (simulating app restart)
        hasher2 = Hasher(last_hash=last_hash_session_1)

        batch2 = [
            AuditEntry(
                timestamp="2024-01-15T10:00:00Z",
                user_id="john",
                action="LOGIN",
                resource="system",
                details="John logged in",
            ),
            AuditEntry(
                timestamp="2024-01-15T10:05:00Z",
                user_id="john",
                action="READ",
                resource="document:report.pdf",
                details="Viewed quarterly report",
            ),
        ]

        hasher2.hash_batch(batch2)

        # Verify batch 2 chains to batch 1
        assert batch2[0].prev_hash == batch1[-1].record_hash

        # Verify complete chain across both batches
        all_entries = batch1 + batch2
        chain_valid, breaks = Hasher.verify_chain(all_entries)
        assert chain_valid, f"Combined chain invalid: {breaks}"

        # Verify each batch independently
        batch_valid, _, _ = Hasher.verify_batch(batch1)
        assert batch_valid

        batch_valid, _, _ = Hasher.verify_batch(batch2)
        assert batch_valid

    def test_tamper_detection(self) -> None:
        """Verify that tampering is detected."""
        hasher = Hasher()

        entries = [
            AuditEntry(
                timestamp="2024-01-15T09:00:00Z",
                user_id="admin",
                action="DELETE",
                resource="user:eve",
                details="Deleted suspicious account",
            ),
            AuditEntry(
                timestamp="2024-01-15T09:01:00Z",
                user_id="admin",
                action="LOGOUT",
                resource="system",
                details="Admin logged out",
            ),
        ]

        hasher.hash_batch(entries)

        # Attacker tries to modify the action
        original_action = entries[0].action
        entries[0].action = "CREATE"  # Tampered!

        # Chain verification still passes (only checks prev_hash links)
        chain_valid, _ = Hasher.verify_chain(entries)
        assert chain_valid  # Chain links are intact

        # But re-hashing reveals tampering
        recomputed_hash = Hasher().hash_record(
            AuditEntry(
                timestamp=entries[0].timestamp,
                user_id=entries[0].user_id,
                action=entries[0].action,  # Tampered value
                resource=entries[0].resource,
                details=entries[0].details,
            )
        )
        assert recomputed_hash != entries[0].record_hash  # Hash mismatch!

        # Restore original
        entries[0].action = original_action

    def test_large_scale_audit_log(self) -> None:
        """Test with a large number of entries across multiple batches."""
        hasher = Hasher()
        all_entries: list[AuditEntry] = []

        # Create 10 batches of 50 entries each
        for batch_num in range(10):
            batch = [
                AuditEntry(
                    timestamp=f"2024-01-15T{batch_num:02d}:{i:02d}:00Z",
                    user_id=f"user_{i % 5}",
                    action=["CREATE", "READ", "UPDATE", "DELETE"][i % 4],
                    resource=f"resource_{i}",
                    details=f"Batch {batch_num} entry {i}",
                )
                for i in range(50)
            ]
            hasher.hash_batch(batch)
            all_entries.extend(batch)

        # Verify entire chain
        chain_valid, breaks = Hasher.verify_chain(all_entries)
        assert chain_valid
        assert len(all_entries) == 500


class TestFinancialTransactionWorkflow:
    """End-to-end test simulating a financial transaction ledger."""

    def test_transaction_ledger(self) -> None:
        """Simulate a transaction ledger with balance verification."""
        hasher = Hasher()

        transactions = [
            Transaction(
                tx_id="TX001",
                from_account="TREASURY",
                to_account="ACC001",
                amount=Decimal("10000.00"),
                currency="USD",
                timestamp="2024-01-15T08:00:00Z",
            ),
            Transaction(
                tx_id="TX002",
                from_account="ACC001",
                to_account="ACC002",
                amount=Decimal("2500.00"),
                currency="USD",
                timestamp="2024-01-15T09:30:00Z",
            ),
            Transaction(
                tx_id="TX003",
                from_account="ACC001",
                to_account="ACC003",
                amount=Decimal("1500.00"),
                currency="USD",
                timestamp="2024-01-15T10:15:00Z",
            ),
            Transaction(
                tx_id="TX004",
                from_account="ACC002",
                to_account="ACC003",
                amount=Decimal("500.00"),
                currency="USD",
                timestamp="2024-01-15T11:00:00Z",
            ),
        ]

        merkle_root = hasher.hash_batch(transactions)

        # All transactions are chained
        chain_valid, breaks = Hasher.verify_chain(transactions)
        assert chain_valid

        # Merkle root is valid
        batch_valid, stored, computed = Hasher.verify_batch(transactions)
        assert batch_valid
        assert stored == merkle_root

        # Each transaction has proper metadata
        for i, tx in enumerate(transactions):
            assert tx.record_hash != ""
            assert tx.batch_sequence == i
            assert tx.batch_id != ""

    def test_cross_batch_transaction_chain(self) -> None:
        """Test transactions spanning multiple settlement batches."""
        hasher = Hasher()
        batches: list[list[Transaction]] = []
        merkle_roots: list[str] = []

        # Morning settlement batch
        morning_batch = [
            Transaction(
                tx_id=f"AM{i:03d}",
                from_account=f"ACC{i:03d}",
                to_account=f"ACC{(i + 1):03d}",
                amount=Decimal(f"{100 * (i + 1)}.00"),
                currency="USD",
                timestamp=f"2024-01-15T0{8 + i}:00:00Z",
            )
            for i in range(3)
        ]
        merkle_roots.append(hasher.hash_batch(morning_batch))
        batches.append(morning_batch)

        # Afternoon settlement batch
        afternoon_batch = [
            Transaction(
                tx_id=f"PM{i:03d}",
                from_account=f"ACC{i + 10:03d}",
                to_account=f"ACC{i + 11:03d}",
                amount=Decimal(f"{200 * (i + 1)}.00"),
                currency="USD",
                timestamp=f"2024-01-15T{14 + i}:00:00Z",
            )
            for i in range(3)
        ]
        merkle_roots.append(hasher.hash_batch(afternoon_batch))
        batches.append(afternoon_batch)

        # Verify cross-batch chaining
        assert afternoon_batch[0].prev_hash == morning_batch[-1].record_hash

        # Verify each batch independently
        for batch in batches:
            batch_valid, _, _ = Hasher.verify_batch(batch)
            assert batch_valid

        # Verify complete chain
        all_transactions = morning_batch + afternoon_batch
        chain_valid, _ = Hasher.verify_chain(all_transactions)
        assert chain_valid


class TestRecoveryScenarios:
    """Test recovery and continuation scenarios."""

    def test_resume_from_checkpoint(self) -> None:
        """Simulate resuming after a crash using the last known hash."""
        # Phase 1: Create initial entries
        hasher = Hasher()
        initial_entries = [
            AuditEntry(
                timestamp=f"2024-01-15T09:0{i}:00Z",
                user_id="system",
                action="INIT",
                resource=f"component_{i}",
                details="Initialization",
            )
            for i in range(5)
        ]
        hasher.hash_batch(initial_entries)

        # Simulate checkpoint: save last hash
        checkpoint_hash = hasher.last_hash

        # Phase 2: Simulate crash and recovery
        # New hasher instance with checkpoint
        recovered_hasher = Hasher(last_hash=checkpoint_hash)

        # Continue adding entries
        new_entries = [
            AuditEntry(
                timestamp=f"2024-01-15T10:0{i}:00Z",
                user_id="system",
                action="PROCESS",
                resource=f"task_{i}",
                details="Processing",
            )
            for i in range(3)
        ]
        recovered_hasher.hash_batch(new_entries)

        # Verify continuity
        assert new_entries[0].prev_hash == initial_entries[-1].record_hash

        # Full chain is valid
        all_entries = initial_entries + new_entries
        chain_valid, _ = Hasher.verify_chain(all_entries)
        assert chain_valid

    def test_verify_historical_data(self) -> None:
        """Simulate verifying historical data loaded from storage."""
        # Simulate: entries loaded from database
        hasher = Hasher()
        stored_entries = [
            AuditEntry(
                timestamp=f"2024-01-{i + 1:02d}T12:00:00Z",
                user_id="auditor",
                action="REVIEW",
                resource=f"report_{i}",
                details=f"Monthly review {i}",
            )
            for i in range(12)
        ]
        hasher.hash_batch(stored_entries)

        # Store the expected values
        expected_merkle_root = stored_entries[-1].batch_merkle_root
        expected_hashes = [e.record_hash for e in stored_entries]

        # Later: verify the stored data hasn't been tampered with
        chain_valid, breaks = Hasher.verify_chain(stored_entries)
        assert chain_valid, "Historical chain has been tampered with"

        batch_valid, stored_root, computed_root = Hasher.verify_batch(stored_entries)
        assert batch_valid, "Historical batch has been tampered with"
        assert stored_root == expected_merkle_root

        # Verify individual hashes
        for entry, expected_hash in zip(stored_entries, expected_hashes, strict=True):
            assert entry.record_hash == expected_hash

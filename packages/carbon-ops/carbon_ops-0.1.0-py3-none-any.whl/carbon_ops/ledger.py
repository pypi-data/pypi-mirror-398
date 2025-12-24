"""Ledger client scaffolding."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Protocol, runtime_checkable


class MerkleTree(Protocol):
    """Minimal protocol required for Merkle tree implementations."""

    def add_leaf(self, value: bytes) -> None: ...

    def root_hash(self) -> bytes: ...

    def proof(self, value: bytes) -> Iterable[bytes]: ...


@dataclass(slots=True)
class LedgerEntry:
    """Represents a carbon emission record destined for the ledger."""

    job_id: str
    timestamp: datetime
    scope: str
    grams_co2e: float
    metadata: dict[str, str]


@runtime_checkable
class SignedMessage(Protocol):
    """Protocol exposing the signature bytes of a signed payload."""

    signature: bytes


@runtime_checkable
class SigningKey(Protocol):
    """Protocol describing the subset of pynacl's ``SigningKey`` used here."""

    def sign(self, data: bytes) -> SignedMessage: ...


class LedgerClient:
    """Placeholder ledger client providing interface contracts."""

    def __init__(self, signer: SigningKey, tree: MerkleTree) -> None:
        self._signer = signer
        self._tree = tree

    def record(self, entry: LedgerEntry) -> dict[str, str]:
        """Record an entry and return signing metadata.

        Real implementation will persist to storage, publish inclusion proofs,
        and generate export artifacts.
        """

        payload = self._serialize(entry)
        signature = self._signer.sign(payload)
        self._tree.add_leaf(signature.signature)
        return {
            "job_id": entry.job_id,
            "signature": signature.signature.hex(),
            "root": self._tree.root_hash().hex(),
        }

    @staticmethod
    def _serialize(entry: LedgerEntry) -> bytes:
        return (
            f"{entry.job_id}|{entry.timestamp.isoformat()}|{entry.scope}|{entry.grams_co2e}|"
            f"{sorted(entry.metadata.items())}".encode("utf-8")
        )

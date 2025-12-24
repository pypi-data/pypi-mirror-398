"""Core package for Carbon Ops Guardrails.

The initial implementation focuses on
- telemetry ingestion contracts
- emission estimation primitives
- tamper-evident ledger interfaces

Concrete services will be added in subsequent iterations.
"""

from .config import CarbonOpsSettings
from .ledger import LedgerClient
from .pipeline import EstimationPipeline

__all__ = ["CarbonOpsSettings", "LedgerClient", "EstimationPipeline"]

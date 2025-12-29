"""
Python implementation of the CPL engine.

Main components:
- ProductionCPLAdapter - Orchestrator for CPL evaluation (file-only mode)
- LocalPolicyCache - In-memory policy cache
- CPLEngine - Core policy evaluation engine
- CPLCondition - Condition parser and evaluator

Future components (not yet integrated):
- PolicySyncManager - For future hot-reloading support
"""

__version__ = "0.1.0"

from .base import CPLCondition, GovernanceDecision, ObservabilityAdapter, RequestData
from .cpl_engine import CPLEngine, CPLEngineManager, ServiceContext
from .local_policy_cache import LocalPolicyCache
from .production_cpl_adapter import ProductionCPLAdapter

# Future: PolicySyncManager for hot-reloading (not yet integrated)
# from .policy_sync_manager import PolicySyncManager

__all__ = [
    "ProductionCPLAdapter",
    "LocalPolicyCache",
    "RequestData",
    "CPLCondition",
    "GovernanceDecision",
    "ObservabilityAdapter",
    "CPLEngine",
    "ServiceContext",
    "CPLEngineManager",
]

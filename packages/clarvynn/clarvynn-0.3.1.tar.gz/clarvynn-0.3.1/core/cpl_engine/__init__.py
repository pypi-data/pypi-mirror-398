"""
CPL Engine - Policy evaluation engine for Clarvynn.

Current implementation:
- python/ - Pure Python implementation (production ready, file-only mode)

Future:
- Hot-reloading via file watching
- Go gRPC server for centralized policy management
"""

# Namespace package
__path__ = __import__("pkgutil").extend_path(__path__, __name__)

# Re-export Python implementation for convenience
from core.cpl_engine.python import (
    CPLCondition,
    CPLEngine,
    CPLEngineManager,
    GovernanceDecision,
    LocalPolicyCache,
    ObservabilityAdapter,
    ProductionCPLAdapter,
    RequestData,
    ServiceContext,
)

__all__ = [
    "CPLEngine",
    "ServiceContext",
    "CPLEngineManager",
    "ProductionCPLAdapter",
    "LocalPolicyCache",
    "RequestData",
    "CPLCondition",
    "GovernanceDecision",
    "ObservabilityAdapter",
]

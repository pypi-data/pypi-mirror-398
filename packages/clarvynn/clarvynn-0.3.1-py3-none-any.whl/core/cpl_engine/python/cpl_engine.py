import os
import random
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .base import CPLCondition, GovernanceDecision, RequestData

# Setup logging
try:
    from clarvynn.logging import get_logger

    logger = get_logger("cpl_engine")
except ImportError:
    import logging

    logger = logging.getLogger(__name__)


@dataclass
class ServiceContext:
    """Context information for a specific service"""

    service_name: str
    namespace: str = "default"
    version: str = "1.0.0"
    environment: str = "production"


@dataclass
class PolicyState:
    """Thread-safe policy state with versioning"""

    policy: Dict[str, Any]
    version: str
    last_updated: float = field(default_factory=time.time)


class CPLEngine:
    """
    Enterprise-scale CPL evaluation engine.

    Features:
    - Dynamic runtime policy updates (thread-safe)
    - Multi-service support with service-specific policies
    - Policy versioning and rollback capability
    - Centralized policy management
    - Hot-reload without service restart
    - Performance optimizations for high throughput
    """

    def __init__(self, service_context: ServiceContext, policy_provider: Optional[Callable] = None):
        self.service_context = service_context
        self.policy_provider = policy_provider

        self._policy_lock = threading.RLock()
        self._policy_state = PolicyState(
            policy={"sampling": {"base_rate": 0.1, "conditions": []}}, version="default"
        )

        self._stats_lock = threading.Lock()
        self._stats = {
            "evaluations": 0,
            "condition_matches": 0,
            "base_rate_decisions": 0,
            "policy_updates": 0,
            "last_policy_update": None,
        }

        self._update_callbacks: List[Callable] = []

        self._condition_cache = {}
        self._cache_lock = threading.Lock()

    def load_policy(self, policy: Dict[str, Any], version: Optional[str] = None) -> bool:
        """
        Load new policy with thread-safe update.
        Returns True if policy was updated, False if same version.
        """
        if version is None:
            version = str(int(time.time()))

        with self._policy_lock:
            if self._policy_state.version == version and self._policy_state.policy == policy:
                return False

            if not self._validate_policy(policy):
                raise ValueError(
                    f"Invalid CPL policy for service {self.service_context.service_name}"
                )

            old_version = self._policy_state.version
            self._policy_state = PolicyState(
                policy=policy, version=version, last_updated=time.time()
            )

            with self._cache_lock:
                self._condition_cache.clear()

            with self._stats_lock:
                self._stats["policy_updates"] += 1
                self._stats["last_policy_update"] = time.time()

            for callback in self._update_callbacks:
                try:
                    callback(old_version, version or "unknown", policy)
                except Exception as e:
                    logger.error(f"Policy update callback failed: {e}")

            logger.info(
                f"🔄 Policy updated for {self.service_context.service_name}: {old_version} → {version}"
            )
            return True

    def evaluate(self, request_data: RequestData) -> GovernanceDecision:
        """
        Evaluate CPL policy against request data (thread-safe).
        Uses current policy version - updates take effect immediately.
        """
        with self._policy_lock:
            current_policy = self._policy_state.policy
            policy_version = self._policy_state.version

        with self._stats_lock:
            self._stats["evaluations"] += 1

        for condition in current_policy.get("sampling", {}).get("conditions", []):
            if self._matches_condition(request_data, condition):
                with self._stats_lock:
                    self._stats["condition_matches"] += 1

                # Matched conditions are ALWAYS sampled at 100%
                # This is the core value prop: never miss critical signals
                return GovernanceDecision(
                    should_sample=True,
                    reason=f"condition_{condition['name']}",
                    rule_name=condition["name"],
                    sampling_rate=1.0,
                )

        with self._stats_lock:
            self._stats["base_rate_decisions"] += 1

        base_rate = current_policy.get("sampling", {}).get("base_rate", 0.1)
        should_sample = random.random() <= base_rate

        return GovernanceDecision(
            should_sample=should_sample,
            reason="base_rate",
            rule_name="base_sampling",
            sampling_rate=base_rate,
        )

    def _matches_condition(self, request_data: RequestData, condition: Dict) -> bool:
        """
        Evaluate if request data matches a CPL condition.
        Uses CPLCondition for robust expression parsing (supports AND/OR/NOT).
        Caches CPLCondition instances for performance.
        """
        condition_key = f"{condition.get('name')}:{condition.get('when')}"

        # Get or create cached CPLCondition
        with self._cache_lock:
            if condition_key not in self._condition_cache:
                self._condition_cache[condition_key] = CPLCondition(condition)
            cpl_condition = self._condition_cache[condition_key]

        # Convert RequestData to attribute dict for CPLCondition
        attrs = self._request_data_to_attrs(request_data)
        return cpl_condition.evaluate(attrs)

    def _request_data_to_attrs(self, request_data: RequestData) -> dict:
        """
        Convert RequestData dataclass to attribute dictionary for CPLCondition.

        This bridges the gap between the structured RequestData format
        and the flexible attribute-based evaluation in CPLCondition.
        """
        attrs = {
            "status_code": request_data.status_code,
            "duration_ms": request_data.duration_ms,
            "duration": request_data.duration_ms,  # Alias for convenience
            "path": request_data.path,
            "method": request_data.method,
            "user_id": request_data.user_id,
            "trace_id": request_data.trace_id,
            "span_name": request_data.span_name,
            "span_kind": request_data.span_kind,
        }
        # Merge custom attributes (they take precedence)
        if request_data.custom_attributes:
            attrs.update(request_data.custom_attributes)
        return attrs

    def _validate_policy(self, policy: Dict[str, Any]) -> bool:
        """Validate policy structure before applying"""
        try:
            if "sampling" not in policy:
                return False

            sampling = policy["sampling"]
            if "base_rate" not in sampling:
                return False

            base_rate = sampling["base_rate"]
            if not (0.0 <= base_rate <= 1.0):
                return False

            for condition in sampling.get("conditions", []):
                # name and when are required
                # Note: rate field is ignored - matched conditions are always 100% sampled
                if not all(key in condition for key in ["name", "when"]):
                    return False

            return True
        except Exception:
            return False

    def add_policy_update_callback(self, callback: Callable):
        """Add callback to be notified of policy updates"""
        self._update_callbacks.append(callback)

    def get_current_policy(self) -> Dict[str, Any]:
        """Get current policy (thread-safe snapshot)"""
        with self._policy_lock:
            return {
                "policy": self._policy_state.policy.copy(),
                "version": self._policy_state.version,
                "last_updated": self._policy_state.last_updated,
            }

    def get_stats(self) -> Dict[str, Any]:
        """Get CPL engine statistics (thread-safe)"""
        with self._stats_lock:
            stats = self._stats.copy()

        stats.update(
            {
                "service_name": self.service_context.service_name,
                "service_namespace": self.service_context.namespace,
                "service_version": self.service_context.version,
                "policy_version": self._policy_state.version,
                "cache_size": len(self._condition_cache),
            }
        )

        return stats


class CPLEngineManager:
    """
    Centralized manager for multiple CPL engines across services.

    Handles:
    - Service discovery and registration
    - Centralized policy distribution
    - Cross-service coordination
    - Policy template management
    """

    def __init__(self):
        self._engines: Dict[str, CPLEngine] = {}
        self._engines_lock = threading.RLock()
        self._policy_templates: Dict[str, Dict] = {}

    def register_service(
        self, service_context: ServiceContext, initial_policy: Optional[Dict] = None
    ) -> CPLEngine:
        """Register a new service and create its CPL engine"""
        service_key = f"{service_context.namespace}:{service_context.service_name}"

        with self._engines_lock:
            if service_key in self._engines:
                return self._engines[service_key]

            engine = CPLEngine(service_context)

            if initial_policy is not None:
                engine.load_policy(initial_policy, "initial")
            elif service_context.service_name in self._policy_templates:
                template = self._policy_templates[service_context.service_name]
                engine.load_policy(template, "template")

            self._engines[service_key] = engine
            logger.info(f"📝 Registered service: {service_key}")
            return engine

    def update_policy_for_service(
        self, namespace: str, service_name: str, policy: Dict, version: Optional[str] = None
    ) -> bool:
        """Update policy for specific service"""
        service_key = f"{namespace}:{service_name}"

        with self._engines_lock:
            if service_key not in self._engines:
                logger.warning(f"⚠️  Service {service_key} not registered")
                return False

            return self._engines[service_key].load_policy(policy, version)

    def update_policy_for_all_services(self, policy: Dict, version: Optional[str] = None) -> int:
        """Update policy for all registered services"""
        updated_count = 0

        with self._engines_lock:
            for service_key, engine in self._engines.items():
                if engine.load_policy(policy, version):
                    updated_count += 1

        logger.info(f"🔄 Updated policy for {updated_count} services")
        return updated_count

    def get_all_stats(self) -> Dict[str, Any]:
        """Get aggregated stats from all services"""
        all_stats = {}

        with self._engines_lock:
            for service_key, engine in self._engines.items():
                all_stats[service_key] = engine.get_stats()

        return all_stats

    def get_service_engine(self, namespace: str, service_name: str) -> Optional[CPLEngine]:
        """Get CPL engine for specific service"""
        service_key = f"{namespace}:{service_name}"

        with self._engines_lock:
            return self._engines.get(service_key)

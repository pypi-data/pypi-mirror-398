from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from dbl_policy import (
    DecisionOutcome,
    Policy,
    PolicyDecision,
    PolicyId,
    PolicyVersion,
    TenantId,
)


# ---------------------------------------------------------------------------
# Policy registry
# Maps policy names to their factory classes
# ---------------------------------------------------------------------------

POLICY_CONTENT_SAFETY = "content-safety"
POLICY_RATE_LIMIT = "rate-limit"
POLICY_BOUNDARY_DEFAULT = "boundary-default"
PIPELINE_MODES = {"minimal", "basic_safety", "standard", "enterprise"}
KNOWN_POLICY_NAMES = {"content_safety", "rate_limit"}

KNOWN_POLICIES = {
    "content_safety": POLICY_CONTENT_SAFETY,
    "rate_limit": POLICY_RATE_LIMIT,
}


# ---------------------------------------------------------------------------
# Default blocked patterns for content safety
# ---------------------------------------------------------------------------

DEFAULT_BLOCKED_PATTERNS = [
    "ignore previous instructions",
    "disregard all prior",
    "bypass security",
    "act as if",
    "pretend you are",
]

STRICT_BLOCKED_PATTERNS = [
    *DEFAULT_BLOCKED_PATTERNS,
    "jailbreak",
    "roleplay",
    "system prompt",
    "developer mode",
]


# ---------------------------------------------------------------------------
# Pipeline Modes with clear semantics
# 
# minimal: No policies (testing only)
# basic_safety: Light content safety only (DEFAULT)
# standard: Balanced safety + rate limiting
# enterprise: Strict safety, strict rate limiting, full audit mode
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PolicyEvaluationResult:
    decisions: tuple[PolicyDecision, ...]
    final_outcome: str
    effective_metadata: dict[str, object]


@dataclass(frozen=True)
class PolicyPipeline:
    name: str
    boundary_id: str
    boundary_version: str
    policy_specs: tuple[dict[str, object], ...]
    policies: tuple[Policy, ...]

    def evaluate(self, context: PolicyContext) -> PolicyEvaluationResult:
        decisions: list[PolicyDecision] = []
        final_outcome = "allow"
        for policy in self.policies:
            decision = policy.evaluate(context)
            decisions.append(decision)
            if decision.outcome == DecisionOutcome.DENY:
                final_outcome = "block"
        if not decisions:
            decisions.append(
                PolicyDecision(
                    outcome=DecisionOutcome.ALLOW,
                    reason_code="boundary.default_allow",
                    reason_message="boundary default allow",
                    policy_id=PolicyId(POLICY_BOUNDARY_DEFAULT),
                    policy_version=PolicyVersion(self.boundary_version),
                    tenant_id=context.tenant_id,
                )
            )
        return PolicyEvaluationResult(
            decisions=tuple(decisions),
            final_outcome=final_outcome,
            effective_metadata={},
        )

    def describe_config(self) -> dict[str, object]:
        return {
            "boundary_id": self.boundary_id,
            "boundary_version": self.boundary_version,
            "pipeline_mode": self.name,
            "policies": list(self.policy_specs),
        }


class ContentSafetyPolicy:
    def __init__(self, blocked_patterns: list[str], content_key: str = "prompt") -> None:
        self._blocked_patterns = [p.lower() for p in blocked_patterns]
        self._content_key = content_key
        self._policy_id = PolicyId(POLICY_CONTENT_SAFETY)
        self._policy_version = PolicyVersion("1.0")

    def evaluate(self, context: PolicyContext) -> PolicyDecision:
        text = str(context.inputs.get(self._content_key, "")).lower()
        for pattern in self._blocked_patterns:
            if pattern in text:
                return PolicyDecision(
                    outcome=DecisionOutcome.DENY,
                    reason_code="content_safety.blocked",
                    reason_message=f"{self._policy_id.value} blocked pattern: {pattern}",
                    policy_id=self._policy_id,
                    policy_version=self._policy_version,
                    tenant_id=context.tenant_id,
                )
        return PolicyDecision(
            outcome=DecisionOutcome.ALLOW,
            reason_code="content_safety.allow",
            reason_message=f"{self._policy_id.value} allowed",
            policy_id=self._policy_id,
            policy_version=self._policy_version,
            tenant_id=context.tenant_id,
        )

    def describe(self) -> dict[str, object]:
        return {
            "policy_id": self._policy_id.value,
            "policy_version": self._policy_version.value,
            "config": {
                "blocked_patterns": list(self._blocked_patterns),
                "content_key": self._content_key,
            },
        }


class RateLimitPolicy:
    def __init__(
        self,
        max_requests: int,
        window_seconds: int,
        rate_checker: Optional[Callable[[str, int], int]] = None,
    ) -> None:
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._rate_checker = rate_checker
        self._policy_id = PolicyId(POLICY_RATE_LIMIT)
        self._policy_version = PolicyVersion("1.0")

    def evaluate(self, context: PolicyContext) -> PolicyDecision:
        if self._rate_checker is None:
            return PolicyDecision(
                outcome=DecisionOutcome.ALLOW,
                reason_code="rate_limit.allow",
                reason_message=f"{self._policy_id.value} allow",
                policy_id=self._policy_id,
                policy_version=self._policy_version,
                tenant_id=context.tenant_id,
            )
        count = self._rate_checker(context.tenant_id.value, self._window_seconds)
        if count > self._max_requests:
            return PolicyDecision(
                outcome=DecisionOutcome.DENY,
                reason_code="rate_limit.exceeded",
                reason_message=f"{self._policy_id.value} exceeded",
                policy_id=self._policy_id,
                policy_version=self._policy_version,
                tenant_id=context.tenant_id,
            )
        return PolicyDecision(
            outcome=DecisionOutcome.ALLOW,
            reason_code="rate_limit.allow",
            reason_message=f"{self._policy_id.value} allow",
            policy_id=self._policy_id,
            policy_version=self._policy_version,
            tenant_id=context.tenant_id,
        )

    def describe(self) -> dict[str, object]:
        return {
            "policy_id": self._policy_id.value,
            "policy_version": self._policy_version.value,
            "config": {
                "max_requests": self._max_requests,
                "window_seconds": self._window_seconds,
            },
        }


def create_pipeline(
    mode: str = "basic_safety",
    enabled_policies: Optional[list[str]] = None,
    boundary_id: str = "dbl-boundary-service",
    boundary_version: str = "0.2.0",
) -> PolicyPipeline:
    """
    Creates a pipeline based on mode and optional policy override.
    
    Modes:
    - minimal: No policies applied (testing only)
    - basic_safety: Light content safety only (DEFAULT)
    - standard: Balanced safety + rate limiting
    - enterprise: Strict safety, strict rate limiting, full audit
    
    Args:
        mode: Preset mode (minimal, basic_safety, standard, enterprise)
        enabled_policies: Optional explicit list of policies (overrides preset)
    
    Returns:
        Configured Pipeline with appropriate policies
    """
    # If explicit policies provided, user override has priority
    if enabled_policies is not None:
        return build_pipeline_from_names(
            enabled_policies,
            boundary_id=boundary_id,
            boundary_version=boundary_version,
        )
    
    # Preset pipelines based on mode
    if mode == "minimal":
        return PolicyPipeline(
            name="minimal",
            boundary_id=boundary_id,
            boundary_version=boundary_version,
            policy_specs=tuple(),
            policies=tuple(),
        )
    
    elif mode == "basic_safety":
        policy = ContentSafetyPolicy(
            blocked_patterns=DEFAULT_BLOCKED_PATTERNS,
            content_key="prompt",
        )
        return PolicyPipeline(
            name="basic_safety",
            boundary_id=boundary_id,
            boundary_version=boundary_version,
            policy_specs=(policy.describe(),),
            policies=(policy,),
        )
    
    elif mode == "standard":
        policy_a = ContentSafetyPolicy(
            blocked_patterns=DEFAULT_BLOCKED_PATTERNS,
            content_key="prompt",
        )
        policy_b = RateLimitPolicy(
            max_requests=100,
            window_seconds=60,
        )
        return PolicyPipeline(
            name="standard",
            boundary_id=boundary_id,
            boundary_version=boundary_version,
            policy_specs=(policy_a.describe(), policy_b.describe()),
            policies=(policy_a, policy_b),
        )
    
    elif mode == "enterprise":
        policy_a = ContentSafetyPolicy(
            blocked_patterns=STRICT_BLOCKED_PATTERNS,
            content_key="prompt",
        )
        policy_b = RateLimitPolicy(
            max_requests=10,
            window_seconds=60,
        )
        return PolicyPipeline(
            name="enterprise",
            boundary_id=boundary_id,
            boundary_version=boundary_version,
            policy_specs=(policy_a.describe(), policy_b.describe()),
            policies=(policy_a, policy_b),
        )
    
    # Fallback: standard (safe default)
    policy_a = ContentSafetyPolicy(
        blocked_patterns=DEFAULT_BLOCKED_PATTERNS,
        content_key="prompt",
    )
    policy_b = RateLimitPolicy(
        max_requests=100,
        window_seconds=60,
    )
    return PolicyPipeline(
        name="standard",
        boundary_id=boundary_id,
        boundary_version=boundary_version,
        policy_specs=(policy_a.describe(), policy_b.describe()),
        policies=(policy_a, policy_b),
    )


def build_pipeline_from_names(
    policy_names: list[str],
    rate_checker: Optional[Callable[[str, int], int]] = None,
    blocked_patterns: Optional[list[str]] = None,
    boundary_id: str = "dbl-boundary-service",
    boundary_version: str = "0.2.0",
) -> PolicyPipeline:
    """
    Builds a pipeline from a list of policy names.
    Used when user explicitly overrides with enabled_policies.
    
    Args:
        policy_names: List of policy identifiers (e.g. ["content_safety", "rate_limit"])
        rate_checker: Optional rate checker for rate_limit policy
        blocked_patterns: Optional patterns for content_safety policy
    """
    policies: list[Policy] = []
    
    for name in policy_names:
        if name not in KNOWN_POLICIES:
            continue
        
        # Instantiate with appropriate config
        if name == "rate_limit":
            policies.append(RateLimitPolicy(
                max_requests=100,
                window_seconds=60,
                rate_checker=rate_checker,
            ))
        elif name == "content_safety":
            policies.append(ContentSafetyPolicy(
                blocked_patterns=blocked_patterns or DEFAULT_BLOCKED_PATTERNS,
                content_key="prompt",
            ))
    
    policy_specs = tuple(p.describe() for p in policies)
    return PolicyPipeline(
        name="custom",
        boundary_id=boundary_id,
        boundary_version=boundary_version,
        policy_specs=policy_specs,
        policies=tuple(policies),
    )


# ---------------------------------------------------------------------------
# Legacy compatibility functions (deprecated)
# ---------------------------------------------------------------------------

def create_default_pipeline(
    max_requests: int = 100,
    window_seconds: int = 60,
    rate_checker: Optional[Callable[[str, int], int]] = None,
    blocked_patterns: Optional[list[str]] = None,
    content_key: str = "prompt",
) -> PolicyPipeline:
    """
    Legacy function for backward compatibility.
    Use create_pipeline("standard") instead.
    """
    return create_pipeline("standard")


def create_minimal_pipeline() -> PolicyPipeline:
    """
    Legacy function for backward compatibility.
    Use create_pipeline("minimal") instead.
    """
    return create_pipeline("minimal")


def create_strict_pipeline(
    blocked_patterns: Optional[list[str]] = None,
) -> PolicyPipeline:
    """
    Legacy function for backward compatibility.
    Use create_pipeline("enterprise") instead.
    """
    return create_pipeline("enterprise")

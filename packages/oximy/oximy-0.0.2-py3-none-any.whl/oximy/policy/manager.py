"""
Policy Manager

Manages policy lifecycle: fetching, caching, and coordinating evaluation.
"""

import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Protocol

import httpx

from ..constants import API_ENDPOINTS
from ..types import (
    OximyConfig,
    OximyState,
    PolicyConfig,
    PolicyDetection,
    PolicyMode,
    PolicyRule,
    PolicyViolation,
    RequestContext,
)
from ..utils import generate_event_id
from .evaluator import (
    EvaluationContext,
    evaluate_rule,
    extract_target_content,
    find_rule_matches,
    modify_target_content,
)
from .redaction import RedactionMatch, apply_redactions
from .stores import PolicyStores, create_policy_stores


class PolicyManager(Protocol):
    """Protocol for PolicyManager type."""

    async def refresh(self) -> None:
        """Fetches and caches policy from API."""
        ...

    async def evaluate_input(
        self,
        request: Any,
        request_context: Optional[RequestContext] = None,
        estimated_cost: Optional[float] = None,
    ) -> "PolicyEvaluationResult":
        """Evaluates input policies before sending to provider."""
        ...

    async def evaluate_output(
        self,
        response: Any,
        request_context: Optional[RequestContext] = None,
    ) -> "PolicyEvaluationResult":
        """Evaluates output policies after receiving from provider."""
        ...

    def get_policy(self) -> PolicyConfig | None:
        """Gets current policy configuration."""
        ...

    def is_enabled(self) -> bool:
        """Checks if policies are enabled."""
        ...

    def get_mode(self) -> PolicyMode:
        """Gets current policy mode."""
        ...

    def get_stores(self) -> PolicyStores:
        """Gets the policy stores (for testing/debugging)."""
        ...

    def dispose(self) -> None:
        """Cleans up resources (call when done with the manager)."""
        ...


@dataclass
class PolicyContext:
    """Policy evaluation context."""

    scope: str  # "input" or "output"
    request: Any = None
    response: Any = None
    request_context: Optional[RequestContext] = None
    stores: Optional[PolicyStores] = None
    estimated_cost: Optional[float] = None


@dataclass
class PolicyEvaluationResult:
    """Result of policy evaluation."""

    allowed: bool = True
    violations: list[PolicyViolation] = field(default_factory=list)
    modified_request: Any = None
    modified_response: Any = None
    blocked: dict[str, str] | None = None


@dataclass
class SlmEvaluationResult:
    """Result from SLM rule evaluation."""

    triggered: bool
    confidence: Optional[float] = None
    matches: Optional[list[dict[str, Any]]] = None
    transformed_content: Optional[str] = None
    detections: Optional[list[PolicyDetection]] = None


async def fetch_policy(
    config: OximyConfig, debug: Callable[..., None]
) -> PolicyConfig | None:
    """Fetches policy configuration from the API."""
    api_url = config.api_url or "https://api.oximy.com"
    url = f"{api_url}{API_ENDPOINTS['POLICY']}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={
                    "Authorization": f"Bearer {config.api_key}",
                },
            )

            if not response.is_success:
                debug("Policy fetch failed:", response.status_code, response.text)
                return None

            data = response.json()

            policy_data = data.get("policy")
            if not policy_data:
                return None

            debug("Policy fetched:", policy_data)

            rules = []
            for rule_data in policy_data.get("rules", []):
                rules.append(
                    PolicyRule(
                        id=rule_data.get("id", ""),
                        enabled=rule_data.get("enabled", True),
                        name=rule_data.get("name", ""),
                        description=rule_data.get("description"),
                        tier=rule_data.get("tier", "local"),  # type: ignore
                        target=rule_data.get("target", {}),
                        match=rule_data.get("match", {}),
                        action=rule_data.get("action", {}),
                        severity=rule_data.get("severity", "medium"),  # type: ignore
                    )
                )

            return PolicyConfig(
                version=policy_data.get("version", 0),
                mode=(policy_data.get("mode") or "shadow"),  # type: ignore
                rules=rules,
            )
    except Exception as error:
        debug("Policy fetch error:", str(error))
        return None


async def evaluate_slm_rule(
    rule: PolicyRule,
    content: str,
    config: OximyConfig,
    debug: Callable[..., None],
    request_context: Optional[RequestContext] = None,
) -> SlmEvaluationResult:
    """Evaluates an SLM rule via the API (single rule)."""
    api_url = config.api_url or "https://api.oximy.com"
    url = f"{api_url}{API_ENDPOINTS['EVALUATE']}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json={
                    "rule_id": rule.id,
                    "content": content,
                    "context": {
                        "scope": rule.target.get("scope", "input"),
                        "userId": request_context.get("user_id") if request_context else None,
                        "sessionId": request_context.get("session_id") if request_context else None,
                    },
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {config.api_key}",
                },
            )

            if not response.is_success:
                debug("SLM evaluation failed:", response.status_code)
                return SlmEvaluationResult(triggered=False)

            data = response.json()

            detections = None
            if data.get("detections"):
                detections = [
                    PolicyDetection(
                        type=d.get("type", ""),
                        value=d.get("value", ""),
                        start=d.get("start", 0),
                        end=d.get("end", 0),
                        confidence=d.get("confidence", 0.0),
                    )
                    for d in data["detections"]
                ]

            return SlmEvaluationResult(
                triggered=data.get("triggered", False),
                confidence=data.get("confidence"),
                matches=data.get("matches"),
                transformed_content=data.get("transformedContent"),
                detections=detections,
            )
    except Exception as error:
        debug("SLM evaluation error:", str(error))
        return SlmEvaluationResult(triggered=False)


async def evaluate_slm_rules_batch(
    rules: list[PolicyRule],
    content: Any,
    config: OximyConfig,
    debug: Callable[..., None],
    request_context: Optional[RequestContext] = None,
) -> Optional[dict[str, Any]]:
    """
    Evaluates multiple SLM rules via a single batched API call.
    This is more efficient when multiple SLM rules need evaluation.
    """
    if not rules:
        return None

    api_url = config.api_url or "https://api.oximy.com"
    url = f"{api_url}{API_ENDPOINTS['EVALUATE']}"

    try:
        request_body = {
            "projectId": config.project_id,
            "requestId": generate_event_id(),
            "content": content,
            "rules": [
                {
                    "id": r.id,
                    "match": r.match,
                    "action": r.action,
                    "target": r.target,
                }
                for r in rules
            ],
            "sessionId": request_context.get("session_id") if request_context else None,
            "context": (
                {
                    "userId": request_context.get("user_id"),
                    "metadata": request_context.get("metadata"),
                }
                if request_context
                else None
            ),
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=request_body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {config.api_key}",
                },
            )

            if not response.is_success:
                debug("SLM batch evaluation failed:", response.status_code)
                return None

            return response.json()
    except Exception as error:
        debug("SLM batch evaluation error:", str(error))
        return None


async def evaluate_policies(
    state: OximyState,
    config: OximyConfig,
    context: PolicyContext,
    debug: Callable[..., None],
) -> PolicyEvaluationResult:
    """Evaluates all policy rules against request/response."""
    result = PolicyEvaluationResult()

    # Check if policies are enabled
    if not state.settings or not state.settings.policy_enabled or not state.policy:
        return result

    policy = state.policy
    mode = state.settings.policy_mode or policy.mode
    data = context.request if context.scope == "input" else context.response

    debug("Evaluating policies:", {
        "mode": mode,
        "scope": context.scope,
        "rule_count": len(policy.rules),
    })

    # Build evaluation context for local rules
    eval_context = EvaluationContext(
        request_context=context.request_context,
        stores=context.stores,
        estimated_cost=context.estimated_cost,
    )

    # Separate rules by scope
    scope_rules = [
        rule
        for rule in policy.rules
        if rule.enabled and rule.target.get("scope") == context.scope
    ]

    # =================================================================
    # 1. Evaluate Blocking Rules (Fail Fast)
    # =================================================================
    block_rules = [r for r in scope_rules if r.action.get("type") == "block"]

    # Local Block Rules
    for rule in [r for r in block_rules if r.tier == "local"]:
        contents = extract_target_content(data, rule.target.get("path", ""))
        for content in contents:
            eval_result = evaluate_rule(rule, content, eval_context)
            if eval_result.triggered and eval_result.violation:
                result.violations.append(eval_result.violation)
                debug("Policy violation (block/local):", rule.name)
                if mode == "enforce":
                    result.allowed = False
                    action = rule.action
                    result.blocked = {
                        "rule_id": rule.id,
                        "rule_name": rule.name,
                        "message": (
                            action.get("message")
                            if isinstance(action, dict)
                            else f"Request blocked by policy: {rule.name}"
                        ),
                    }
                    return result

    # SLM Block Rules
    slm_block_rules = [r for r in block_rules if r.tier == "slm"]
    if mode == "enforce":
        for rule in slm_block_rules:
            contents = extract_target_content(data, rule.target.get("path", ""))
            for content in contents:
                slm_result = await evaluate_slm_rule(rule, content, config, debug, context.request_context)
                if slm_result.triggered:
                    violation = PolicyViolation(
                        rule_id=rule.id,
                        rule_name=rule.name,
                        action=rule.action.get("type", "block"),  # type: ignore
                        severity=rule.severity,  # type: ignore
                        matched=slm_result.matches[0].get("text") if slm_result.matches else None,
                        detections=slm_result.detections,
                    )
                    result.violations.append(violation)
                    debug("Policy violation (block/slm):", rule.name)
                    result.allowed = False
                    action = rule.action
                    result.blocked = {
                        "rule_id": rule.id,
                        "rule_name": rule.name,
                        "message": (
                            action.get("message")
                            if isinstance(action, dict)
                            else f"Request blocked by policy: {rule.name}"
                        ),
                    }
                    return result
    else:
        # Shadow Mode SLM Block Rules (Background)
        async def check_slm_block(rule: PolicyRule, content: str) -> None:
            res = await evaluate_slm_rule(rule, content, config, debug, context.request_context)
            if res.triggered:
                debug("Policy violation (block/slm/shadow):", rule.name)

        for rule in slm_block_rules:
            contents = extract_target_content(data, rule.target.get("path", ""))
            for content in contents:
                asyncio.create_task(check_slm_block(rule, content))

    # =================================================================
    # 2. Evaluate Alert Rules
    # =================================================================
    alert_rules = [r for r in scope_rules if r.action.get("type") == "alert"]
    for rule in [r for r in alert_rules if r.tier == "local"]:
        contents = extract_target_content(data, rule.target.get("path", ""))
        for content in contents:
            eval_result = evaluate_rule(rule, content, eval_context)
            if eval_result.triggered and eval_result.violation:
                result.violations.append(eval_result.violation)
                debug("Policy alert (local):", rule.name)

    # =================================================================
    # 3. Evaluate Redaction Rules
    # =================================================================
    redact_rules = [r for r in scope_rules if r.action.get("type") == "redact"]

    if mode == "enforce" and redact_rules:
        # Separate rules by redaction method
        simple_redact_rules = [
            r for r in redact_rules
            if not r.action.get("method") or r.action.get("method") == "simple"
        ]
        advanced_redact_rules = [
            r for r in redact_rules
            if r.action.get("method") in ("pseudoanonymize", "mask")
        ]

        current_data = data

        # Handle simple redaction locally (grouped by path)
        if simple_redact_rules:
            rules_by_path: dict[str, list[PolicyRule]] = {}
            for r in simple_redact_rules:
                path = r.target.get("path", "")
                if path not in rules_by_path:
                    rules_by_path[path] = []
                rules_by_path[path].append(r)

            for path, rules in rules_by_path.items():
                # Apply all rules for this path in one pass per content item
                async def modifier(content: str, rules: list[PolicyRule] = rules) -> str:
                    matches: list[RedactionMatch] = []

                    # Collect Local Matches (simple redaction)
                    for rule in [r for r in rules if r.tier == "local"]:
                        rule_matches = find_rule_matches(rule, content)
                        if rule_matches:
                            result.violations.append(
                                PolicyViolation(
                                    rule_id=rule.id,
                                    rule_name=rule.name,
                                    action=rule.action.get("type", "redact"),  # type: ignore
                                    severity=rule.severity,  # type: ignore
                                    matched=rule_matches[0].get("matched"),
                                )
                            )
                            action = rule.action
                            replacement = (
                                action.get("replacement")
                                if isinstance(action, dict)
                                else "[REDACTED]"
                            )
                            matches.extend(
                                RedactionMatch(
                                    start=m["start"],
                                    end=m["end"],
                                    replacement=replacement or "[REDACTED]",
                                    source=rule.name,
                                )
                                for m in rule_matches
                            )

                    # Collect SLM Matches (simple redaction only)
                    for rule in [r for r in rules if r.tier == "slm"]:
                        slm_result = await evaluate_slm_rule(
                            rule, content, config, debug, context.request_context
                        )
                        if slm_result.triggered and slm_result.matches:
                            result.violations.append(
                                PolicyViolation(
                                    rule_id=rule.id,
                                    rule_name=rule.name,
                                    action=rule.action.get("type", "redact"),  # type: ignore
                                    severity=rule.severity,  # type: ignore
                                    matched=slm_result.matches[0].get("text") if slm_result.matches else None,
                                    detections=slm_result.detections,
                                )
                            )
                            action = rule.action
                            replacement = (
                                action.get("replacement")
                                if isinstance(action, dict)
                                else "[REDACTED]"
                            )
                            matches.extend(
                                RedactionMatch(
                                    start=m["start"],
                                    end=m["end"],
                                    replacement=replacement or "[REDACTED]",
                                    source=rule.name,
                                )
                                for m in slm_result.matches
                            )

                    return apply_redactions(content, matches)

                current_data = await modify_target_content(current_data, path, modifier)

        # Handle advanced redaction via API (pseudoanonymize, mask)
        if advanced_redact_rules:
            slm_advanced_rules = [r for r in advanced_redact_rules if r.tier == "slm"]
            if slm_advanced_rules:
                batch_result = await evaluate_slm_rules_batch(
                    slm_advanced_rules,
                    current_data,
                    config,
                    debug,
                    context.request_context,
                )

                if batch_result:
                    # Apply transformed content from API
                    if batch_result.get("transformedContent"):
                        current_data = batch_result["transformedContent"]

                    # Record violations
                    for evaluation in batch_result.get("evaluations", []):
                        if evaluation.get("matched"):
                            rule = next(
                                (r for r in slm_advanced_rules if r.id == evaluation.get("ruleId")),
                                None,
                            )
                            if rule:
                                detections = None
                                if evaluation.get("detections"):
                                    detections = [
                                        PolicyDetection(
                                            type=d.get("type", ""),
                                            value=d.get("value", ""),
                                            start=d.get("start", 0),
                                            end=d.get("end", 0),
                                            confidence=d.get("confidence", 0.0),
                                        )
                                        for d in evaluation["detections"]
                                    ]
                                result.violations.append(
                                    PolicyViolation(
                                        rule_id=rule.id,
                                        rule_name=rule.name,
                                        action=rule.action.get("type", "redact"),  # type: ignore
                                        severity=rule.severity,  # type: ignore
                                        detections=detections,
                                    )
                                )

        if current_data != data:
            if context.scope == "input":
                result.modified_request = current_data
            else:
                result.modified_response = current_data
    else:
        # Shadow Mode Redaction (Just evaluate and log)
        # Local
        for rule in [r for r in redact_rules if r.tier == "local"]:
            contents = extract_target_content(data, rule.target.get("path", ""))
            for content in contents:
                eval_result = evaluate_rule(rule, content, eval_context)
                if eval_result.triggered and eval_result.violation:
                    result.violations.append(eval_result.violation)
                    debug("Policy violation (redact/local/shadow):", rule.name)
        # SLM (Background)
        async def check_slm_redact(rule: PolicyRule, content: str) -> None:
            res = await evaluate_slm_rule(rule, content, config, debug, context.request_context)
            if res.triggered:
                debug("Policy violation (redact/slm/shadow):", rule.name)

        for rule in [r for r in redact_rules if r.tier == "slm"]:
            contents = extract_target_content(data, rule.target.get("path", ""))
            for content in contents:
                asyncio.create_task(check_slm_redact(rule, content))

    return result


def create_policy_manager(
    config: OximyConfig, state: OximyState, debug: Callable[..., None]
) -> PolicyManager:
    """Creates a policy manager bound to config and state."""

    # Create local stores for rate and cost limiting
    stores = create_policy_stores()

    class PolicyManagerImpl:
        """Policy manager instance."""

        async def refresh(self) -> None:
            """Fetches and caches policy from API."""
            if state.settings and state.settings.policy_enabled:
                state.policy = await fetch_policy(config, debug)

        async def evaluate_input(
            self,
            request: Any,
            request_context: Optional[RequestContext] = None,
            estimated_cost: Optional[float] = None,
        ) -> PolicyEvaluationResult:
            """Evaluates input policies before sending to provider."""
            return await evaluate_policies(
                state,
                config,
                PolicyContext(
                    scope="input",
                    request=request,
                    request_context=request_context,
                    stores=stores,
                    estimated_cost=estimated_cost,
                ),
                debug,
            )

        async def evaluate_output(
            self,
            response: Any,
            request_context: Optional[RequestContext] = None,
        ) -> PolicyEvaluationResult:
            """Evaluates output policies after receiving from provider."""
            return await evaluate_policies(
                state,
                config,
                PolicyContext(
                    scope="output",
                    response=response,
                    request_context=request_context,
                    stores=stores,
                ),
                debug,
            )

        def get_policy(self) -> PolicyConfig | None:
            """Gets current policy configuration."""
            return state.policy

        def is_enabled(self) -> bool:
            """Checks if policies are enabled."""
            return state.settings.policy_enabled if state.settings else False

        def get_mode(self) -> PolicyMode:
            """Gets current policy mode."""
            return state.settings.policy_mode if state.settings else "shadow"  # type: ignore

        def get_stores(self) -> PolicyStores:
            """Gets the policy stores (for testing/debugging)."""
            return stores

        def dispose(self) -> None:
            """Cleans up resources (call when done with the manager)."""
            stores.rate_limit_store.clear()
            stores.cost_store.clear()

    return PolicyManagerImpl()

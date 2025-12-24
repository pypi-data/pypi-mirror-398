"""
Policy Rule Evaluator

Evaluates local policy rules (regex, lists, limits).
Does not handle SLM rules - those go through the API.
"""

import asyncio
import json
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional

from ..types import PolicyMatch, PolicyRule, PolicyViolation, RequestContext

if TYPE_CHECKING:
    from .stores import PolicyStores


@dataclass
class EvaluationContext:
    """Context for rule evaluation including stores and request context."""

    path: Optional[str] = None
    request_context: Optional[RequestContext] = None
    stores: Optional["PolicyStores"] = None
    estimated_cost: Optional[float] = None


class EvaluationResult:
    """Result of evaluating a single rule."""

    def __init__(
        self,
        triggered: bool,
        violation: PolicyViolation | None = None,
        matched_content: str | None = None,
        match_start: int | None = None,
        match_end: int | None = None,
    ):
        self.triggered = triggered
        self.violation = violation
        self.matched_content = matched_content
        self.match_start = match_start
        self.match_end = match_end


def evaluate_rule(
    rule: PolicyRule, content: str, context: EvaluationContext | None = None
) -> EvaluationResult:
    """Evaluates a policy rule against content."""
    if not rule.enabled:
        return EvaluationResult(triggered=False)

    # Only evaluate local rules here
    if rule.tier != "local":
        return EvaluationResult(triggered=False)

    match = rule.match
    result: EvaluationResult

    match_type = match.get("type") if isinstance(match, dict) else None

    if match_type == "regex":
        result = evaluate_regex(content, match)
    elif match_type == "deny_list":
        result = evaluate_deny_list(content, match)
    elif match_type == "allow_list":
        result = evaluate_allow_list(content, match)
    elif match_type == "contains":
        result = evaluate_contains(content, match)
    elif match_type == "token_limit":
        result = evaluate_token_limit(content, match)
    elif match_type == "rate_limit":
        result = evaluate_rate_limit(match, context)
    elif match_type == "cost_limit":
        result = evaluate_cost_limit(match, context)
    else:
        # Unknown match type or requires API (ai_model, ai_custom)
        return EvaluationResult(triggered=False)

    if result.triggered:
        action = rule.action
        action_type = action.get("type") if isinstance(action, dict) else "alert"
        result.violation = PolicyViolation(
            rule_id=rule.id,
            rule_name=rule.name,
            action=action_type,  # type: ignore
            severity=rule.severity,  # type: ignore
            matched=result.matched_content,
            message=action.get("message") if isinstance(action, dict) and action_type == "block" else None,
        )

    return result


def evaluate_regex(content: str, match: dict[str, Any]) -> EvaluationResult:
    """Evaluates regex match."""
    try:
        pattern = match.get("pattern", "")
        flags = match.get("flags", "g")
        # Convert JS regex flags to Python
        python_flags = 0
        if "i" in flags:
            python_flags |= re.IGNORECASE
        if "m" in flags:
            python_flags |= re.MULTILINE

        regex = re.compile(pattern, python_flags)
        result = regex.search(content)

        if result:
            return EvaluationResult(
                triggered=True,
                matched_content=result.group(0),
                match_start=result.start(),
                match_end=result.end(),
            )
    except Exception:
        # Invalid regex, don't trigger
        pass

    return EvaluationResult(triggered=False)


def evaluate_deny_list(content: str, match: dict[str, Any]) -> EvaluationResult:
    """Evaluates deny list match. Triggers if content contains ANY item in the deny list."""
    case_sensitive = match.get("case_sensitive", False)
    search_content = content if case_sensitive else content.lower()
    values = match.get("values", [])

    for value in values:
        search_value = value if case_sensitive else value.lower()
        index = search_content.find(search_value)

        if index != -1:
            return EvaluationResult(
                triggered=True,
                matched_content=content[index : index + len(value)],
                match_start=index,
                match_end=index + len(value),
            )

    return EvaluationResult(triggered=False)


def evaluate_allow_list(content: str, match: dict[str, Any]) -> EvaluationResult:
    """Evaluates allow list match. Triggers if content does NOT match any item in the allow list."""
    case_sensitive = match.get("case_sensitive", True)
    search_content = content if case_sensitive else content.lower()
    values = match.get("values", [])

    for value in values:
        search_value = value if case_sensitive else value.lower()

        # Support wildcards (e.g., "gpt-4o*" matches "gpt-4o-2024-05-13")
        if value.endswith("*"):
            prefix = search_value[:-1]
            if search_content.startswith(prefix):
                return EvaluationResult(triggered=False)
        elif search_content == search_value:
            return EvaluationResult(triggered=False)

    # Not in allow list - trigger
    return EvaluationResult(triggered=True, matched_content=content)


def evaluate_contains(content: str, match: dict[str, Any]) -> EvaluationResult:
    """Evaluates contains match. Triggers if content contains ANY of the specified values."""
    case_sensitive = match.get("case_sensitive", False)
    search_content = content if case_sensitive else content.lower()
    values = match.get("values", [])

    for value in values:
        search_value = value if case_sensitive else value.lower()
        index = search_content.find(search_value)

        if index != -1:
            return EvaluationResult(
                triggered=True,
                matched_content=content[index : index + len(value)],
                match_start=index,
                match_end=index + len(value),
            )

    return EvaluationResult(triggered=False)


def evaluate_token_limit(content: str, match: dict[str, Any]) -> EvaluationResult:
    """Evaluates token limit. Uses rough estimate of 4 chars per token."""
    max_tokens = match.get("max_tokens", 0)
    estimated_tokens = (len(content) + 3) // 4

    if estimated_tokens > max_tokens:
        return EvaluationResult(
            triggered=True,
            matched_content=f"{estimated_tokens} tokens (limit: {max_tokens})",
        )

    return EvaluationResult(triggered=False)


def evaluate_rate_limit(
    match: dict[str, Any], context: EvaluationContext | None = None
) -> EvaluationResult:
    """
    Evaluates rate limit.
    Triggers if the request count exceeds the limit within the time window.
    """
    from .stores import parse_window

    if context is None or context.stores is None:
        # No store available, can't evaluate rate limits
        return EvaluationResult(triggered=False)

    store = context.stores.rate_limit_store

    try:
        window_ms = parse_window(match.get("window", "1h"))
        request_context = context.request_context

        # Build the key based on the match.key field
        key_value = "global"
        key_field = match.get("key")
        if key_field and request_context:
            context_value = request_context.get(key_field)
            if isinstance(context_value, str):
                key_value = context_value

        store_key = f"rate:{key_field or 'global'}:{key_value}"
        count = store.increment(store_key, window_ms)

        if count > match.get("limit", 0):
            return EvaluationResult(
                triggered=True,
                matched_content=f"{count}/{match.get('limit', 0)} requests in {match.get('window', '')}",
            )
    except Exception:
        # Invalid window format, don't trigger
        pass

    return EvaluationResult(triggered=False)


def evaluate_cost_limit(
    match: dict[str, Any], context: EvaluationContext | None = None
) -> EvaluationResult:
    """
    Evaluates cost limit.
    Triggers if the cumulative cost exceeds the limit within the time window.
    """
    from .stores import parse_window

    if context is None or context.stores is None:
        # No store available, can't evaluate cost limits
        return EvaluationResult(triggered=False)

    store = context.stores.cost_store

    try:
        window_ms = parse_window(match.get("window", "24h"))
        request_context = context.request_context
        estimated_cost = context.estimated_cost or 0.0

        # Build the key based on the match.key field
        key_value = "global"
        key_field = match.get("key")
        if key_field and request_context:
            context_value = request_context.get(key_field)
            if isinstance(context_value, str):
                key_value = context_value

        store_key = f"cost:{key_field or 'global'}:{key_value}"
        total_cost = store.add(store_key, estimated_cost, window_ms)

        max_cost = match.get("max_cost_usd", 0.0)
        if total_cost > max_cost:
            return EvaluationResult(
                triggered=True,
                matched_content=f"${total_cost:.4f} / ${max_cost:.2f} in {match.get('window', '')}",
            )
    except Exception:
        # Invalid window format, don't trigger
        pass

    return EvaluationResult(triggered=False)


def extract_target_content(data: Any, path: str) -> list[str]:
    """Extracts content from a target path in the request/response."""
    contents: list[str] = []

    if not isinstance(data, dict):
        return contents

    # Handle common paths
    if path == "model" and isinstance(data.get("model"), str):
        contents.append(data["model"])
        return contents

    # Handle messages[*].content
    if "messages" in path and isinstance(data.get("messages"), list):
        for msg in data["messages"]:
            if isinstance(msg, dict):
                # Check role filter (e.g., "messages[?role='user'].content")
                role_match = re.search(r"\?\s*role\s*=\s*['\"](\w+)['\"]", path)
                if role_match and msg.get("role") != role_match.group(1):
                    continue

                # Extract content
                content = msg.get("content")
                if isinstance(content, str):
                    contents.append(content)
                elif isinstance(content, list):
                    # Handle content blocks
                    for block in content:
                        if isinstance(block, dict):
                            text = block.get("text")
                            if isinstance(text, str):
                                contents.append(text)
        return contents

    # Handle tools[*].function.name
    if "tools" in path and isinstance(data.get("tools"), list):
        for tool in data["tools"]:
            if isinstance(tool, dict):
                func = tool.get("function")
                if isinstance(func, dict):
                    name = func.get("name")
                    if isinstance(name, str):
                        contents.append(name)
        return contents

    # Handle tool_calls
    if "tool_call" in path or "tool_calls" in path:
        # Check in choices
        if isinstance(data.get("choices"), list):
            for choice in data["choices"]:
                if isinstance(choice, dict):
                    message = choice.get("message")
                    if isinstance(message, dict):
                        tool_calls = message.get("tool_calls")
                        if isinstance(tool_calls, list):
                            for tc in tool_calls:
                                if isinstance(tc, dict):
                                    func = tc.get("function")
                                    if isinstance(func, dict):
                                        if "name" in path and isinstance(func.get("name"), str):
                                            contents.append(func["name"])
                                        if "arguments" in path and isinstance(func.get("arguments"), str):
                                            contents.append(func["arguments"])
        return contents

    # Handle MCP servers
    if path == "servers" or "mcp" in path:
        # MCP servers would be in a custom field
        mcp_servers = data.get("mcp_servers")
        if isinstance(mcp_servers, list):
            contents.extend(s for s in mcp_servers if isinstance(s, str))
        return contents

    # Generic path extraction (simple dot notation)
    parts = path.split(".")
    current: Any = data
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            break

    if isinstance(current, str):
        contents.append(current)

    return contents


def apply_redaction(content: str, start: int, end: int, replacement: str) -> str:
    """Applies redaction to content."""
    return content[:start] + replacement + content[end:]


def find_rule_matches(rule: PolicyRule, content: str) -> list[dict[str, Any]]:
    """Finds all matches for a rule in the content. Returns all occurrences."""
    matches: list[dict[str, Any]] = []

    if not rule.enabled or rule.tier != "local":
        return matches

    match = rule.match
    match_type = match.get("type") if isinstance(match, dict) else None

    if match_type == "regex":
        try:
            pattern = match.get("pattern", "")
            flags = match.get("flags", "g")
            python_flags = 0
            if "i" in flags:
                python_flags |= re.IGNORECASE
            if "m" in flags:
                python_flags |= re.MULTILINE
            # Ensure global flag for loop
            if "g" not in flags:
                flags += "g"

            regex = re.compile(pattern, python_flags)
            for result in regex.finditer(content):
                matches.append({
                    "start": result.start(),
                    "end": result.end(),
                    "matched": result.group(0),
                })
        except Exception:
            pass
    elif match_type in ("deny_list", "contains"):
        case_sensitive = match.get("case_sensitive", False)
        search_content = content if case_sensitive else content.lower()
        values = match.get("values", [])

        for value in values:
            search_value = value if case_sensitive else value.lower()
            index = search_content.find(search_value)
            while index != -1:
                matches.append({
                    "start": index,
                    "end": index + len(value),
                    "matched": content[index : index + len(value)],
                })
                index = search_content.find(search_value, index + 1)

    return matches


async def modify_target_content(
    data: Any, path: str, modifier: Any
) -> Any:
    """Modifies content at the target path using a modifier function. Returns a deep clone of data with modifications applied."""
    if not isinstance(data, dict):
        return data

    # Deep clone
    cloned = json.loads(json.dumps(data))

    # Handle common paths
    if path == "model" and isinstance(cloned.get("model"), str):
        if asyncio.iscoroutinefunction(modifier):
            cloned["model"] = await modifier(cloned["model"])
        else:
            cloned["model"] = modifier(cloned["model"])
        return cloned

    # Handle messages[*].content
    if "messages" in path and isinstance(cloned.get("messages"), list):
        for msg in cloned["messages"]:
            if isinstance(msg, dict):
                # Check role filter
                role_match = re.search(r"\?\s*role\s*=\s*['\"](\w+)['\"]", path)
                if role_match and msg.get("role") != role_match.group(1):
                    continue

                # Extract content
                content = msg.get("content")
                if isinstance(content, str):
                    if asyncio.iscoroutinefunction(modifier):
                        msg["content"] = await modifier(content)
                    else:
                        msg["content"] = modifier(content)
                elif isinstance(content, list):
                    # Handle content blocks
                    for block in content:
                        if isinstance(block, dict):
                            text = block.get("text")
                            if isinstance(text, str):
                                if asyncio.iscoroutinefunction(modifier):
                                    block["text"] = await modifier(text)
                                else:
                                    block["text"] = modifier(text)
        return cloned

    # Handle tools[*].function.name
    if "tools" in path and isinstance(cloned.get("tools"), list):
        for tool in cloned["tools"]:
            if isinstance(tool, dict):
                func = tool.get("function")
                if isinstance(func, dict):
                    name = func.get("name")
                    if isinstance(name, str):
                        if asyncio.iscoroutinefunction(modifier):
                            func["name"] = await modifier(name)
                        else:
                            func["name"] = modifier(name)
        return cloned

    # Handle tool_calls
    if "tool_call" in path or "tool_calls" in path:
        if isinstance(cloned.get("choices"), list):
            for choice in cloned["choices"]:
                if isinstance(choice, dict):
                    message = choice.get("message")
                    if isinstance(message, dict):
                        tool_calls = message.get("tool_calls")
                        if isinstance(tool_calls, list):
                            for tc in tool_calls:
                                if isinstance(tc, dict):
                                    func = tc.get("function")
                                    if isinstance(func, dict):
                                        if "name" in path and isinstance(func.get("name"), str):
                                            if asyncio.iscoroutinefunction(modifier):
                                                func["name"] = await modifier(func["name"])
                                            else:
                                                func["name"] = modifier(func["name"])
                                        if "arguments" in path and isinstance(func.get("arguments"), str):
                                            if asyncio.iscoroutinefunction(modifier):
                                                func["arguments"] = await modifier(func["arguments"])
                                            else:
                                                func["arguments"] = modifier(func["arguments"])
        return cloned

    # Handle MCP servers
    if (path == "servers" or "mcp" in path) and isinstance(cloned.get("mcp_servers"), list):
        new_servers = []
        for s in cloned["mcp_servers"]:
            if isinstance(s, str):
                if asyncio.iscoroutinefunction(modifier):
                    new_servers.append(await modifier(s))
                else:
                    new_servers.append(modifier(s))
            else:
                new_servers.append(s)
        cloned["mcp_servers"] = new_servers
        return cloned

    # Generic path extraction (simple dot notation)
    parts = path.split(".")
    current: dict[str, Any] = cloned

    for i in range(len(parts) - 1):
        part = parts[i]
        if isinstance(current.get(part), dict):
            current = current[part]
        else:
            # Path doesn't exist
            return cloned

    last_part = parts[-1]
    if isinstance(current.get(last_part), str):
        if asyncio.iscoroutinefunction(modifier):
            current[last_part] = await modifier(current[last_part])
        else:
            current[last_part] = modifier(current[last_part])

    return cloned

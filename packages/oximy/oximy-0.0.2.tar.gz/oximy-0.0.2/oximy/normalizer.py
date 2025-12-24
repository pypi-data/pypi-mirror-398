"""
Data Normalizer

Converts provider-specific request/response formats to canonical format.
"""

from typing import Any

from .types import (
    EventType,
    NormalizedData,
    NormalizedInput,
    NormalizedOutput,
    NormalizedTools,
    NormalizedUsage,
    Provider,
)
from .utils import calculate_content_length


def normalize_data(
    request: Any, response: Any, provider: Provider, event_type: EventType
) -> NormalizedData:
    """Normalizes request and response data."""
    normalized: NormalizedData = {}

    # Extract model info
    model_info = extract_model_info(request, response)
    if model_info:
        normalized["model"] = model_info

    # Extract input summary
    input_summary = extract_input_summary(request, event_type)
    if input_summary:
        normalized["input"] = input_summary

    # Extract output summary
    output_summary = extract_output_summary(response, event_type)
    if output_summary:
        normalized["output"] = output_summary

    # Extract tools
    tools = extract_tools(request, response)
    if tools:
        normalized["tools"] = tools

    # Extract usage (cost calculation is done server-side)
    usage = extract_usage(response, provider)
    if usage:
        normalized["usage"] = usage

    return normalized


def extract_model_info(request: Any, response: Any) -> dict[str, str] | None:
    """Extracts model information from request and response."""
    result: dict[str, str] = {}

    # Get requested model from request
    if isinstance(request, dict):
        if isinstance(request.get("model"), str):
            result["requested"] = request["model"]

    # Get actual model from response
    if isinstance(response, dict):
        if isinstance(response.get("model"), str):
            result["used"] = response["model"]

    # If no used model, fall back to requested
    if "used" not in result and "requested" in result:
        result["used"] = result["requested"]

    return result if result else None


def extract_input_summary(request: Any, event_type: EventType) -> NormalizedInput | None:
    """Extracts input summary from request."""
    if not isinstance(request, dict):
        return None

    input_data: NormalizedInput = {"type": "other"}

    # Handle messages array (OpenAI, Anthropic)
    if "messages" in request and isinstance(request["messages"], list):
        input_data["type"] = "messages"
        input_data["message_count"] = len(request["messages"])

        roles: list[str] = []
        content_length = 0
        has_system = False
        has_images = False

        for msg in request["messages"]:
            if isinstance(msg, dict):
                # Collect roles
                role = msg.get("role")
                if isinstance(role, str) and role not in roles:
                    roles.append(role)
                    if role == "system":
                        has_system = True

                # Calculate content length
                content_length += calculate_content_length(msg.get("content"))

                # Check for images
                content = msg.get("content")
                if isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict):
                            part_type = part.get("type")
                            if part_type in ("image_url", "image"):
                                has_images = True

        input_data["roles"] = roles
        input_data["content_length"] = content_length
        input_data["has_system"] = has_system
        input_data["has_images"] = has_images

        return input_data

    # Handle text input (Responses API, embeddings)
    if isinstance(request.get("input"), str):
        input_data["type"] = "text"
        input_data["content_length"] = len(request["input"])
        return input_data

    # Handle array input (embeddings batch)
    if isinstance(request.get("input"), list):
        input_data["type"] = "text_array"
        input_data["item_count"] = len(request["input"])
        input_data["content_length"] = sum(
            len(item) if isinstance(item, str) else 0 for item in request["input"]
        )
        return input_data

    # Handle prompt (image generation)
    if isinstance(request.get("prompt"), str):
        input_data["type"] = "text"
        input_data["content_length"] = len(request["prompt"])
        return input_data

    # Handle Anthropic system message
    if isinstance(request.get("system"), str):
        input_data["has_system"] = True

    return input_data if input_data["type"] != "other" else None


def extract_output_summary(response: Any, event_type: EventType) -> NormalizedOutput | None:
    """Extracts output summary from response."""
    if not isinstance(response, dict):
        return None

    output_data: NormalizedOutput = {"type": "other"}

    # Handle choices array (OpenAI chat completions)
    if "choices" in response and isinstance(response["choices"], list):
        output_data["type"] = "message" if len(response["choices"]) == 1 else "messages"
        output_data["choice_count"] = len(response["choices"])

        content_length = 0
        finish_reason: str | None = None

        for choice in response["choices"]:
            if isinstance(choice, dict):
                # Get finish reason from first choice
                if not finish_reason and isinstance(choice.get("finish_reason"), str):
                    finish_reason = choice["finish_reason"]

                # Get content from message
                message = choice.get("message")
                if isinstance(message, dict):
                    content_length += calculate_content_length(message.get("content"))

                    # Check for tool calls
                    if isinstance(message.get("tool_calls"), list) and len(message.get("tool_calls", [])) > 0:
                        output_data["type"] = "tool_calls"

        output_data["content_length"] = content_length
        if finish_reason:
            output_data["finish_reason"] = finish_reason

        return output_data

    # Handle content array (Anthropic)
    if "content" in response and isinstance(response["content"], list):
        output_data["type"] = "message"
        output_data["choice_count"] = 1

        content_length = 0
        for block in response["content"]:
            if isinstance(block, dict):
                if isinstance(block.get("text"), str):
                    content_length += len(block["text"])
                if block.get("type") == "tool_use":
                    output_data["type"] = "tool_calls"

        output_data["content_length"] = content_length

        if isinstance(response.get("stop_reason"), str):
            output_data["finish_reason"] = response["stop_reason"]

        return output_data

    # Handle embeddings
    if "data" in response and isinstance(response["data"], list) and event_type == "embedding":
        embeddings = response["data"]
        output_data["type"] = "embeddings" if len(embeddings) > 1 else "embedding"
        output_data["choice_count"] = len(embeddings)

        # Get embedding dimensions from first item
        if len(embeddings) > 0 and isinstance(embeddings[0], dict):
            embedding = embeddings[0].get("embedding")
            if isinstance(embedding, list):
                output_data["embedding_dimensions"] = len(embedding)

        return output_data

    # Handle image generation
    if "data" in response and isinstance(response["data"], list) and event_type == "image":
        output_data["type"] = "image_url"
        output_data["image_count"] = len(response["data"])

        # Check if b64
        if len(response["data"]) > 0 and isinstance(response["data"][0], dict):
            if response["data"][0].get("b64_json"):
                output_data["type"] = "image_b64"

        return output_data

    return output_data if output_data["type"] != "other" else None


def extract_tools(request: Any, response: Any) -> NormalizedTools | None:
    """Extracts tool information from request and response."""
    tools: NormalizedTools = {
        "available": {"count": 0, "names": []},
        "called": {"count": 0, "calls": []},
    }

    # Extract available tools from request
    if isinstance(request, dict):
        if isinstance(request.get("tools"), list):
            tools["available"]["count"] = len(request["tools"])
            names = []
            for tool in request["tools"]:
                if isinstance(tool, dict):
                    func = tool.get("function")
                    if isinstance(func, dict):
                        name = func.get("name")
                        if isinstance(name, str):
                            names.append(name)
            tools["available"]["names"] = names

        # Count tool results in request (for multi-turn)
        if isinstance(request.get("messages"), list):
            tool_results = [
                msg
                for msg in request["messages"]
                if isinstance(msg, dict) and msg.get("role") == "tool"
            ]

            if tool_results:
                tools["results"] = {"count": len(tool_results)}

    # Extract tool calls from response
    if isinstance(response, dict):
        # OpenAI format
        if isinstance(response.get("choices"), list):
            for choice in response["choices"]:
                if isinstance(choice, dict):
                    message = choice.get("message")
                    if isinstance(message, dict):
                        tool_calls = message.get("tool_calls")
                        if isinstance(tool_calls, list):
                            calls = []
                            for tc in tool_calls:
                                if isinstance(tc, dict):
                                    func = tc.get("function")
                                    if isinstance(func, dict):
                                        calls.append({
                                            "id": tc.get("id") if isinstance(tc.get("id"), str) else None,
                                            "name": func.get("name", "unknown"),
                                            "arguments_size": len(func.get("arguments", "")) if isinstance(func.get("arguments"), str) else None,
                                        })
                            tools["called"]["calls"] = calls
                            tools["called"]["count"] = len(calls)

        # Anthropic format
        if isinstance(response.get("content"), list):
            calls = []
            for block in response["content"]:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    calls.append({
                        "id": block.get("id") if isinstance(block.get("id"), str) else None,
                        "name": block.get("name", "unknown"),
                        "arguments_size": len(str(block.get("input", {}))) if isinstance(block.get("input"), dict) else None,
                    })
            tools["called"]["calls"] = calls
            tools["called"]["count"] = len(calls)

    # Only return if there's actual tool activity
    if (
        tools["available"]["count"] > 0
        or tools["called"]["count"] > 0
        or "results" in tools
    ):
        return tools

    return None


def extract_usage(response: Any, provider: Provider) -> NormalizedUsage | None:
    """Extracts token usage from response."""
    if not isinstance(response, dict):
        return None

    usage_data: NormalizedUsage = {}

    # Get usage object
    usage_obj = response.get("usage")
    if not isinstance(usage_obj, dict):
        return None

    # Handle different provider formats
    # OpenAI format: prompt_tokens, completion_tokens
    if isinstance(usage_obj.get("prompt_tokens"), (int, float)):
        usage_data["input_tokens"] = int(usage_obj["prompt_tokens"])
    if isinstance(usage_obj.get("completion_tokens"), (int, float)):
        usage_data["output_tokens"] = int(usage_obj["completion_tokens"])

    # Anthropic/Responses API format: input_tokens, output_tokens
    if isinstance(usage_obj.get("input_tokens"), (int, float)):
        usage_data["input_tokens"] = int(usage_obj["input_tokens"])
    if isinstance(usage_obj.get("output_tokens"), (int, float)):
        usage_data["output_tokens"] = int(usage_obj["output_tokens"])

    # Total tokens
    if isinstance(usage_obj.get("total_tokens"), (int, float)):
        usage_data["total_tokens"] = int(usage_obj["total_tokens"])
    elif "input_tokens" in usage_data and "output_tokens" in usage_data:
        usage_data["total_tokens"] = usage_data["input_tokens"] + usage_data["output_tokens"]

    # Cached tokens (OpenAI prompt caching)
    prompt_details = usage_obj.get("prompt_tokens_details")
    if isinstance(prompt_details, dict):
        if isinstance(prompt_details.get("cached_tokens"), (int, float)):
            usage_data["cached_tokens"] = int(prompt_details["cached_tokens"])

    # Anthropic cache
    if isinstance(usage_obj.get("cache_read_input_tokens"), (int, float)):
        usage_data["cached_tokens"] = int(usage_obj["cache_read_input_tokens"])

    # Reasoning tokens (o1 models)
    completion_details = usage_obj.get("completion_tokens_details")
    if isinstance(completion_details, dict):
        if isinstance(completion_details.get("reasoning_tokens"), (int, float)):
            usage_data["reasoning_tokens"] = int(completion_details["reasoning_tokens"])

    return usage_data if usage_data else None

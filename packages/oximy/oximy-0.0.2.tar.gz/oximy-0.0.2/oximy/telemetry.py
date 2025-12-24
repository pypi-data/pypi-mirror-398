"""
Telemetry Sender

Handles sending events to the Oximy API.
Fire-and-forget with fail-open behavior.
"""

import asyncio
from typing import Any, Callable

import httpx

from .constants import API_ENDPOINTS, DEFAULT_TIMEOUT_MS
from .types import (
    EventResponse,
    InitResponse,
    OximyConfig,
    OximyEvent,
    OximyState,
    PolicyConfig,
    PolicyMode,
    PolicyRule,
    ProjectSettings,
)


async def send_event(
    event: OximyEvent,
    config: OximyConfig,
    state: OximyState,
    debug: Callable[..., None],
) -> EventResponse | None:
    """Sends a telemetry event to the Oximy API. Fire-and-forget: does not block, does not throw."""
    api_url = config.api_url or "https://api.oximy.com"
    timeout = config.timeout or DEFAULT_TIMEOUT_MS

    # Skip if telemetry is disabled
    if state.settings and not state.settings.telemetry_enabled:
        debug("Telemetry disabled, skipping event:", event["id"])
        return None

    url = f"{api_url}{API_ENDPOINTS['EVENTS']}"

    try:
        async with httpx.AsyncClient(timeout=timeout / 1000.0) as client:
            response = await client.post(
                url,
                json=event,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {config.api_key}",
                    "X-Project-Id": config.project_id,
                },
            )

            if not response.is_success:
                debug("Telemetry send failed:", response.status_code, response.text)
                return None

            data = response.json()
            debug("Telemetry sent:", event["id"], "config_version:", data.get("config_version"))

            # Check for config version change
            if state.settings and data.get("config_version") != state.settings.config_version:
                debug("Config version changed, triggering refresh")
                # Trigger background refresh (non-blocking)
                asyncio.create_task(refresh_init(config, state, debug))

            return EventResponse(
                received=data.get("received", True),
                event_id=data.get("event_id", event["id"]),
                config_version=data.get("config_version", 0),
            )
    except Exception as error:
        # Fail-open: silently ignore all errors
        if isinstance(error, httpx.TimeoutException):
            debug("Telemetry send timed out")
        else:
            debug("Telemetry send error:", str(error))
        return None


async def fetch_init(
    config: OximyConfig, debug: Callable[..., None]
) -> tuple[ProjectSettings, PolicyConfig | None]:
    """Fetches project settings and policies from /v1/init. Single API call used during SDK initialization."""
    api_url = config.api_url or "https://api.oximy.com"
    url = f"{api_url}{API_ENDPOINTS['INIT']}"

    default_settings = ProjectSettings(
        project_id=config.project_id,
        project_name="Unknown",
        config_version=0,
        telemetry_enabled=True,
        policy_enabled=False,
        policy_mode="shadow",
    )

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={
                    "Authorization": f"Bearer {config.api_key}",
                    "X-Project-Id": config.project_id,
                },
            )

            if not response.is_success:
                debug("Init fetch failed:", response.status_code, response.text)
                return default_settings, None

            data = response.json()
            debug("Init response:", data)

            settings = ProjectSettings(
                project_id=data.get("project_id") or config.project_id,
                project_name=data.get("project_name") or "Unknown",
                config_version=data.get("config_version") or data.get("config_version", 0),
                telemetry_enabled=data.get("settings", {}).get("telemetry_enabled", True),
                policy_enabled=data.get("settings", {}).get("policy_enabled", False),
                policy_mode=(data.get("settings", {}).get("policy_mode") or "shadow")  # type: ignore
            )

            # Parse policy if present and enabled
            policy: PolicyConfig | None = None
            if settings.policy_enabled and data.get("policy"):
                policy_data = data["policy"]
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
                policy = PolicyConfig(
                    version=policy_data.get("version", 0),
                    mode=(policy_data.get("mode") or settings.policy_mode),  # type: ignore
                    rules=rules,
                )

            return settings, policy
    except Exception as error:
        debug("Init fetch error:", str(error))
        return default_settings, None


async def refresh_init(
    config: OximyConfig, state: OximyState, debug: Callable[..., None]
) -> None:
    """Refreshes settings and policies in the background. Used when config version changes."""
    settings, policy = await fetch_init(config, debug)
    state.settings = settings
    state.policy = policy
    debug("Settings refreshed:", settings)


def create_telemetry_sender(
    config: OximyConfig,
    state: OximyState,
    debug: Callable[..., None],
) -> Callable[[OximyEvent], None]:
    """Creates a telemetry sender bound to config and state."""

    def send(event: OximyEvent) -> None:
        # Fire and forget - don't await
        asyncio.create_task(send_event(event, config, state, debug))

    return send

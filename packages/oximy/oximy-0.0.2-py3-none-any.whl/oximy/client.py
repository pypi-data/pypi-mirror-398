"""
Oximy Client

Main entry point for the Oximy SDK.
Provides a clean API for wrapping AI clients with telemetry and policies.
"""

import asyncio
from typing import Any

from .constants import SDK_VERSION
from .policy import PolicyManager, create_policy_manager
from .telemetry import create_telemetry_sender, fetch_init
from .types import OximyConfig, OximyState, PolicyConfig, ProjectSettings
from .utils import create_debug_logger
from .wrapper import wrap_client


class Oximy:
    """
    Oximy SDK client.

    Example:
        ```python
        from oximy import Oximy
        from openai import OpenAI

        oximy = Oximy(
            api_key="ox_xxx",
            project_id="proj_xxx",
        )

        openai = oximy.wrap(OpenAI())

        response = await openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello"}],
        )
        ```
    """

    def __init__(
        self,
        api_key: str | OximyConfig | None = None,
        project_id: str | None = None,
        config: OximyConfig | None = None,
        **kwargs: Any,
    ):
        """
        Creates a new Oximy client.
        
        Args:
            api_key: Oximy API key, or OximyConfig object (required if config not provided)
            project_id: Project ID (required if config not provided)
            config: OximyConfig object (alternative to keyword arguments)
            **kwargs: Additional config options (environment, service, version, etc.)
        """
        # Support OximyConfig as first positional argument (backwards compatibility)
        if isinstance(api_key, OximyConfig):
            config = api_key
            api_key = None
        
        # Support both config object and keyword arguments
        if config:
            oximy_config = config
        else:
            # Build config from keyword arguments
            if not api_key:
                raise ValueError("Oximy: api_key is required")
            if not project_id:
                raise ValueError("Oximy: project_id is required")
            
            oximy_config = OximyConfig(
                api_key=api_key,
                project_id=project_id,
                environment=kwargs.get("environment"),
                service=kwargs.get("service"),
                version=kwargs.get("version"),
                metadata=kwargs.get("metadata"),
                api_url=kwargs.get("api_url", "https://api.oximy.com"),
                timeout=kwargs.get("timeout", 100),
                debug=kwargs.get("debug", False),
                on_policy_violation=kwargs.get("on_policy_violation"),
                on_error=kwargs.get("on_error"),
            )
        
        # Validate required config
        if not oximy_config.api_key:
            raise ValueError("Oximy: api_key is required")
        if not oximy_config.project_id:
            raise ValueError("Oximy: project_id is required")

        self._config = oximy_config
        self._debug = create_debug_logger(oximy_config.debug or False)

        # Initialize state
        self._state = OximyState(
            config=oximy_config,
            settings=None,
            initialized=False,
            policy=None,
        )

        self._policy_manager: PolicyManager | None = None
        self._init_task: asyncio.Task | None = None

        self._debug("Oximy client created:", {
            "project_id": oximy_config.project_id,
            "api_url": oximy_config.api_url or "https://api.oximy.com",
        })

        # Start initialization lazily (only when event loop is available)
        self._init_task = None
        try:
            loop = asyncio.get_running_loop()
            # Event loop exists, create task
            self._init_task = loop.create_task(self._initialize())
        except RuntimeError:
            # No event loop running, will initialize on first wrap call
            pass

    async def _initialize(self) -> None:
        """Initializes the SDK by fetching project settings and policies from /v1/init."""
        if self._state.initialized:
            return

        self._debug("Initializing...")

        try:
            # Fetch settings and policies in one call
            settings, policy = await fetch_init(self._config, self._debug)

            self._state.settings = settings
            self._state.policy = policy

            self._debug("Settings loaded:", settings)
            if self._state.policy:
                self._debug("Policy loaded:", self._state.policy)

            # Create policy manager
            self._policy_manager = create_policy_manager(self._config, self._state, self._debug)

            self._state.initialized = True
            self._debug("Initialized successfully")
        except Exception as error:
            self._debug("Initialization error:", error)
            # Fail-open: set default settings and continue
            self._state.settings = ProjectSettings(
                project_id=self._config.project_id,
                project_name="Unknown",
                config_version=0,
                telemetry_enabled=True,
                policy_enabled=False,
                policy_mode="shadow",
            )
            self._policy_manager = create_policy_manager(self._config, self._state, self._debug)
            self._state.initialized = True

    def wrap(self, client: Any) -> Any:
        """
        Wraps an AI client with Oximy telemetry and policy evaluation.

        Args:
            client: The AI client to wrap (OpenAI, Anthropic, etc.)

        Returns:
            The wrapped client with the same interface

        Example:
            ```python
            openai = oximy.wrap(OpenAI())
            anthropic = oximy.wrap(Anthropic())
            ```
        """
        # Ensure initialization task is started if not already
        if self._init_task is None:
            try:
                loop = asyncio.get_running_loop()
                self._init_task = loop.create_task(self._initialize())
            except RuntimeError:
                # No event loop, initialize with defaults
                self._wait_for_init()

        # Wait for initialization if not complete
        if not self._state.initialized:
            # Block synchronously on first wrap call
            # This ensures settings are loaded before any requests
            self._wait_for_init()

        send_event = create_telemetry_sender(self._config, self._state, self._debug)
        return wrap_client(
            client,
            send_event,
            self._config,
            self._state,
            self._debug,
            self._policy_manager,
        )

    def _wait_for_init(self) -> None:
        """Synchronously waits for initialization."""
        if self._state.initialized:
            return

        # For the blocking init, we need to handle it differently
        # In Python, we can't truly block on a coroutine synchronously
        # So we'll just mark as initialized with default settings
        # The actual settings will be fetched async and updated
        if not self._state.settings:
            self._state.settings = ProjectSettings(
                project_id=self._config.project_id,
                project_name="Unknown",
                config_version=0,
                telemetry_enabled=True,
                policy_enabled=False,
                policy_mode="shadow",
            )
        if not self._policy_manager:
            self._policy_manager = create_policy_manager(self._config, self._state, self._debug)
        self._state.initialized = True

    def get_settings(self) -> ProjectSettings | None:
        """Gets the current project settings."""
        return self._state.settings

    def get_policy(self) -> PolicyConfig | None:
        """Gets the current policy configuration."""
        return self._state.policy

    def is_enabled(self) -> bool:
        """Checks if telemetry is enabled."""
        return self._state.settings.telemetry_enabled if self._state.settings else True

    def is_policy_enabled(self) -> bool:
        """Checks if policies are enabled."""
        return self._state.settings.policy_enabled if self._state.settings else False

    def get_policy_mode(self) -> str:
        """Gets the current policy mode."""
        return self._state.settings.policy_mode if self._state.settings else "shadow"  # type: ignore

    def get_config(self) -> OximyConfig:
        """Gets the current configuration."""
        return self._config

    async def refresh(self) -> None:
        """Refreshes settings and policies from the server."""
        self._debug("Refreshing settings and policies...")
        settings, policy = await fetch_init(self._config, self._debug)
        self._state.settings = settings
        self._state.policy = policy
        self._debug("Refresh complete")


async def create_oximy(config: OximyConfig) -> Oximy:
    """
    Creates an Oximy client asynchronously.
    Use this when you need to ensure initialization is complete before proceeding.

    Example:
        ```python
        oximy = await create_oximy(
            api_key="ox_xxx",
            project_id="proj_xxx",
        )

        # Initialization is guaranteed complete
        openai = oximy.wrap(OpenAI())
        ```
    """
    client = Oximy(config)
    # Wait for initialization to complete
    if client._init_task:
        await client._init_task
    return client

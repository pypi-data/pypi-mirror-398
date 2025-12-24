"""
Oximy SDK Constants
"""

# SDK version
SDK_VERSION = "0.0.2"

# SDK language identifier
SDK_LANGUAGE = "python"

# Default Oximy API base URL
DEFAULT_API_URL = "https://api.oximy.com"

# Default timeout for telemetry requests in milliseconds
DEFAULT_TIMEOUT_MS = 100

# Event ID prefix
EVENT_ID_PREFIX = "evt_"

# Provider base URLs for auto-detection
PROVIDER_BASE_URLS = {
    "api.openai.com": "openai",
    "api.anthropic.com": "anthropic",
    "generativelanguage.googleapis.com": "google",
    "api.mistral.ai": "mistral",
    "api.cohere.ai": "cohere",
    "openrouter.ai": "openrouter",
    "api.groq.com": "groq",
    "api.together.xyz": "together",
    "api.fireworks.ai": "fireworks",
    "api.perplexity.ai": "perplexity",
}

# Azure OpenAI URL pattern
AZURE_OPENAI_PATTERN = r"\.openai\.azure\.com"

# AWS Bedrock URL pattern
BEDROCK_PATTERN = r"bedrock.*\.amazonaws\.com"

# Ollama default URL
OLLAMA_PATTERN = r"localhost:11434|127\.0\.0\.1:11434"

# API endpoints
API_ENDPOINTS = {
    "INIT": "/v1/init",
    "EVENTS": "/v1/events",
    "POLICY": "/v1/policy",
    "EVALUATE": "/v1/evaluate",
}

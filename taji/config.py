"""Central configuration and constants for Taji 1.1."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Identity
# ---------------------------------------------------------------------------
APP_NAME = "Taji 1.1"
APP_VERSION = "1.1.0"
APP_TAGLINE = "Private local AI research assistant"

# ---------------------------------------------------------------------------
# Model / Ollama
# ---------------------------------------------------------------------------
OLLAMA_HOST = "http://127.0.0.1:11434"
MODEL_NAME = "qwen2.5:3b"

# Higher temp prevents the 3B model from being overly robotic or mute
DEFAULT_TEMPERATURE = 0.6
DEFAULT_NUM_CTX = 8192
DEFAULT_TIMEOUT = 120.0

# ---------------------------------------------------------------------------
# Research
# ---------------------------------------------------------------------------
# How many results to request from the search backend.
SEARCH_MAX_RESULTS = 6
# How many distinct sources to gather and feed to the model.
# Keep low for 3B models so they don't lose focus.
MAX_SOURCES = 4
# Max characters of fetched page text kept per source.
MAX_SOURCE_CHARS = 2500
# Network timeout for search and fetch requests (seconds).
FETCH_TIMEOUT = 20.0

# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
WINDOW_TITLE = APP_NAME
WINDOW_SIZE = (1120, 780)
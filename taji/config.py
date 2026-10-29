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

# Lower temperature keeps answers grounded and reduces hallucination.
DEFAULT_TEMPERATURE = 0.3
DEFAULT_NUM_CTX = 8192
DEFAULT_TIMEOUT = 120.0

# ---------------------------------------------------------------------------
# Research
# ---------------------------------------------------------------------------
# How many results to request from the search backend.
SEARCH_MAX_RESULTS = 8
# How many distinct sources to gather and feed to the model.
MAX_SOURCES = 6
# Max characters of fetched page text kept per source.
MAX_SOURCE_CHARS = 4000
# How many rounds of query expansion the research engine performs (>=2 adds sub-queries).
RESEARCH_DEPTH = 2
# Network timeout for search and fetch requests (seconds).
FETCH_TIMEOUT = 20.0

# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
WINDOW_TITLE = APP_NAME
WINDOW_SIZE = (1120, 780)

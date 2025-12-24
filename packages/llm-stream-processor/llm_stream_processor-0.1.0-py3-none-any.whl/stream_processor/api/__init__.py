"""
Public API for llm_stream_processor.

Includes the streaming decorator and helper callback actions.
"""
from .decorator import llm_stream_processor
from .actions import (
    drop,
    continuous_drop,
    continuous_pass,
    replace,
    passthrough,
    halt,
)

__all__ = [
    "llm_stream_processor",
    "drop",
    "continuous_drop",
    "continuous_pass",
    "replace",
    "passthrough",
    "halt",
]
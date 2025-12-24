"""
Helper callback actions for llm_stream_processor.
"""
from ..engine.types import ActionDecision, ActionType

def drop(ctx=None) -> ActionDecision:
    """Callback helper: drop the matched keyword."""
    return ActionDecision(ActionType.DROP)

def continuous_drop(ctx=None) -> ActionDecision:
    """Start dropping all subsequent content until CONTINUE_PASS."""
    return ActionDecision(ActionType.CONTINUE_DROP)

def continuous_pass(ctx=None) -> ActionDecision:
    """Resume passing content after a drop segment until CONTINUE_DROP."""
    return ActionDecision(ActionType.CONTINUE_PASS)

def replace(text: str) -> ActionDecision:
    """Replace the matched keyword with the provided text."""
    return ActionDecision(ActionType.REPLACE, replacement=text)

def passthrough(ctx=None) -> ActionDecision:
    """Leave the matched keyword in place (no-op)."""
    return ActionDecision(ActionType.PASS)

def halt(ctx=None) -> ActionDecision:
    """Abort the stream immediately."""
    return ActionDecision(ActionType.HALT)
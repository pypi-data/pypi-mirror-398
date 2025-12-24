"""
Defines action types and decisions for keyword matches.

ActionType enumerates the possible outcomes from callbacks:
  PASS, DROP, REPLACE, HALT, CONTINUE_DROP, CONTINUE_PASS.

ActionDecision encapsulates a callback's choice, optionally with replacement text.
"""
from enum import Enum, auto
from typing import Optional

class ActionType(Enum):
    PASS = auto()
    DROP = auto()
    REPLACE = auto()
    HALT = auto()
    CONTINUE_DROP = auto()
    CONTINUE_PASS = auto()

class ActionDecision:
    """
    Represents the decision taken by a callback on a detected keyword.

    Attributes:
      type: an ActionType value.
      replacement: optional text for REPLACE actions.
    """
    __slots__ = ('type', 'replacement')

    def __init__(self, type: ActionType, replacement: Optional[str] = None):
        self.type = type
        self.replacement = replacement
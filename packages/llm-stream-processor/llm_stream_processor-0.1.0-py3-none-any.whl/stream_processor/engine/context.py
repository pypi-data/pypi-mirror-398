"""
ActionContext: provides context to callbacks on keyword match.

This context includes the matched keyword, the current buffer contents,
absolute position in the stream, and optional history tracking of all
inputs, outputs, and past actions.
"""
from typing import List
from .history import StreamHistory

class ActionContext:
    """
    Contains information about a triggered keyword match for callbacks.

    Attributes:
      keyword: the matched pattern string.
      buffer: characters buffered (including the matched keyword).
      absolute_pos: current position in the input stream (1-based).
      history: StreamHistory for querying past inputs/outputs/actions.
    """
    __slots__ = (
        'keyword',        # matched keyword
        'buffer',         # current buffer contents (list of chars)
        'absolute_pos',   # position in input stream (1-based)
        'history',        # StreamHistory instance for full history
    )

    def __init__(self, keyword: str, buffer: List[str], absolute_pos: int, history: StreamHistory):
        self.keyword = keyword
        self.buffer = buffer
        self.absolute_pos = absolute_pos
        self.history = history
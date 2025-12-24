"""
Stream and action history tracking.
"""
from typing import List, Tuple
from .types import ActionDecision

class StreamHistory:
    """
    Tracks the full input, output, and action history for a stream.
    Provides APIs for callbacks to query past context.
    """
    __slots__ = ('_inputs', '_outputs', '_actions')

    def __init__(self):
        self._inputs: List[str] = []
        self._outputs: List[str] = []
        self._actions: List[Tuple[int, str, ActionDecision]] = []

    def record_input(self, ch: str) -> None:
        self._inputs.append(ch)

    def record_output(self, ch: str) -> None:
        self._outputs.append(ch)

    def record_action(self, pos: int, keyword: str, decision: ActionDecision) -> None:
        self._actions.append((pos, keyword, decision))

    def get_inputs(self) -> List[str]:
        return list(self._inputs)

    def get_outputs(self) -> List[str]:
        return list(self._outputs)

    def get_actions(self) -> List[Tuple[int, str, ActionDecision]]:
        return list(self._actions)

class NullHistory:
    """
    No-op history collector for disabled history mode.
    """
    __slots__ = ()

    def record_input(self, ch: str) -> None:
        pass

    def record_output(self, ch: str) -> None:
        pass

    def record_action(self, pos: int, keyword: str, decision: ActionDecision) -> None:
        pass

    def get_inputs(self) -> List[str]:
        return []

    def get_outputs(self) -> List[str]:
        return []

    def get_actions(self) -> List[Tuple[int, str, ActionDecision]]:
        return []
"""
StreamProcessor: core streaming engine for character-level filtering.

This processor uses an Aho–Corasick automaton (built by KeywordRegistry)
to detect registered keywords in a character stream lazily. On each match,
configured callbacks decide to PASS, DROP, REPLACE, HALT, CONTINUE_DROP,
or CONTINUE_PASS. The processor maintains a buffer of recent characters
to ensure prefix safety and performs lazy flushing when safe.
"""
from collections import deque
from typing import List
from .registry import KeywordRegistry
from .history import StreamHistory, NullHistory
from .context import ActionContext
from .types import ActionDecision, ActionType
from .exceptions import StreamHalted


class StreamProcessor:
    """
    Processes a character stream, emitting filtered characters based on registered keywords.
    """

    def __init__(self, registry: KeywordRegistry, *, record_history: bool = True):
        """
        Initialize the StreamProcessor.

        Args:
            registry: a compiled KeywordRegistry with failure trie.
            record_history: if True, track input/output/actions history;
                            otherwise use no-op stub to save memory.
        """
        self._registry = registry
        # Ensure the automaton is compiled
        if not registry._compiled:
            registry.compile()
        # Automaton root and maximum keyword length for lazy flush
        self._root = registry._root  # type: ignore
        self._max_len = registry._max_len
        # Current Aho–Corasick state
        self._node = self._root
        # Buffer for recent characters (up to max keyword length)
        self._buffer: deque = deque()
        # Absolute position in the input stream
        self._pos: int = 0
        # History tracker (real or no-op)
        if record_history:
            self._history = StreamHistory()
        else:
            self._history = NullHistory()
        # Drop mode suppresses output until CONTINUE_PASS
        self._drop_mode = False
        # Flag indicating a HALT decision occurred
        self._halted = False

    def process(self, ch: str) -> List[str]:  # pragma: no cover
        """
        Process a single character and return output characters.

        Steps:
          1. Record input and append to buffer.
          2. Advance Aho–Corasick state (follow fail links if needed).
          3. If node has matches, select longest keyword and invoke callbacks:
             - CONTINUE_DROP: enter drop mode, flush prior buffer.
             - CONTINUE_PASS: exit drop mode, flush matched marker.
             - DROP: remove keyword from buffer.
             - REPLACE: remove keyword and append replacement.
             - PASS: no-op.
             - HALT: remove keyword, mark halted, and raise StreamHalted.
          4. Reset state to root after a match to allow overlaps.
          5. Lazy flush: if buffer > max_len, emit or drop oldest char.

        Args:
            ch: incoming character to process.

        Returns:
            A list of characters (possibly empty) to emit.

        Raises:
            StreamHalted: if any callback returns HALT.
        """
        out: List[str] = []
        # 1) Record input history and buffer the character
        self._history.record_input(ch)
        self._buffer.append(ch)
        self._pos += 1

        # 2) Aho–Corasick state transition: follow failure links
        while ch not in self._node.children and self._node is not self._root:
            self._node = self._node.fail  # type: ignore
        self._node = self._node.children.get(ch, self._root)  # type: ignore

        # 3) Handle matches at current node
        if self._node.output:
            # Pick the longest matching keyword to resolve overlaps
            kw, callbacks = max(self._node.output, key=lambda x: len(x[0]))
            for cb in callbacks:
                # Prepare context for callback
                ctx = ActionContext(
                    keyword=kw,
                    buffer=list(self._buffer),
                    absolute_pos=self._pos,
                    history=self._history,
                )
                decision = cb(ctx)
                # None from callback means PASS
                if decision is None:
                    continue
                # Record action and apply decision
                self._history.record_action(self._pos, kw, decision)
                if decision.type is ActionType.CONTINUE_DROP:
                    # Enter drop mode: flush prior buffer on first entry
                    if not self._drop_mode:
                        all_buf = list(self._buffer)
                        self._buffer.clear()
                        prior = all_buf[:-len(kw)] if len(kw) <= len(all_buf) else []
                        for c in prior:
                            self._history.record_output(c)
                            out.append(c)
                    self._drop_mode = True
                elif decision.type is ActionType.CONTINUE_PASS:
                    # Exit drop mode: flush only the matched keyword marker
                    if self._drop_mode:
                        all_buf = list(self._buffer)
                        self._buffer.clear()
                        marker = all_buf[-len(kw):] if len(kw) <= len(all_buf) else all_buf
                        for c in marker:
                            self._history.record_output(c)
                            out.append(c)
                    self._drop_mode = False
                elif decision.type is ActionType.DROP:
                    # Remove matched keyword from buffer
                    for _ in range(len(kw)):
                        if self._buffer:
                            self._buffer.pop()
                elif decision.type is ActionType.REPLACE:
                    # Remove keyword and inject replacement text
                    for _ in range(len(kw)):
                        if self._buffer:
                            self._buffer.pop()
                    if decision.replacement:
                        for rc in decision.replacement:
                            self._buffer.append(rc)
                elif decision.type is ActionType.PASS:
                    # Leave buffer unchanged
                    pass
                elif decision.type is ActionType.HALT:
                    # Remove matched keyword, mark halt, and abort
                    for _ in range(len(kw)):
                        if self._buffer:
                            self._buffer.pop()
                    self._halted = True
                    raise StreamHalted()
            # 4) Reset state to root to allow overlapping matches
            self._node = self._root

        # 5) Lazy flush: emit or drop oldest if buffer exceeds max keyword length
        if len(self._buffer) > self._max_len:
            c = self._buffer.popleft()
            if not self._drop_mode:
                self._history.record_output(c)
                out.append(c)
        return out

    def flush(self) -> List[str]:
        """
        Flush and return all remaining buffered characters.

        If a HALT decision occurred, returns the buffer as-is unless drop mode
        is active. When drop mode is active after a halt, all buffered
        characters are discarded. Otherwise applies drop-mode or normal flush
        logic.

        Returns:
            Remaining characters to emit after processing the entire input.
        """
        # If halted, emit remaining buffer unless drop mode is active
        if getattr(self, '_halted', False):
            rem = list(self._buffer)
            self._buffer.clear()
            if self._drop_mode:
                return []
            return rem
        # If in drop mode, discard all buffered characters
        if self._drop_mode:
            self._buffer.clear()
            return []
        # Normal flush: emit all buffered characters
        rem = list(self._buffer)
        for c in rem:
            self._history.record_output(c)
        self._buffer.clear()
        return rem

"""
KeywordRegistry: A registry of keywords and their associated callbacks.

This module builds an Aho–Corasick trie for efficient multi-pattern matching.
Users can register and deregister keyword callbacks, then compile the trie.
"""
from typing import Callable, Dict, List, Optional
from .trie import _Node
from .context import ActionContext
from .types import ActionDecision

class KeywordRegistry:
    """
    Registry for keywords and their associated callbacks.

    Methods:
      - register(keyword, callback): add a callback for a keyword.
      - deregister(keyword, callback=None): remove a specific or all callbacks.
      - compile(): build the Aho–Corasick automaton (trie + failure links).
      - max_len(): get the length of the longest registered keyword.
    """
    def __init__(self):
        self._keywords: Dict[str, List[Callable[[ActionContext], ActionDecision]]] = {}
        self._compiled: bool = False
        self._root: Optional[_Node] = None
        self._max_len: int = 0

    def register(self, keyword: str, callback: Callable[[ActionContext], ActionDecision]) -> None:
        """
        Register a callback for a given keyword.
        """
        # Validate inputs
        if not isinstance(keyword, str) or not keyword:
            raise ValueError("keyword must be a non-empty string")
        if not callable(callback):
            raise TypeError("callback must be callable")
        # Register callback
        if keyword in self._keywords:
            self._keywords[keyword].append(callback)
        else:
            self._keywords[keyword] = [callback]
        self._compiled = False

    def deregister(self, keyword: str, callback: Optional[Callable[[ActionContext], ActionDecision]] = None) -> None:
        """
        Deregister a callback or all callbacks for a given keyword.
        """
        # Validate inputs
        if not isinstance(keyword, str) or not keyword:
            raise ValueError("keyword must be a non-empty string")
        if callback is not None and not callable(callback):
            raise TypeError("callback must be callable or None")
        if keyword not in self._keywords:
            return
        if callback is None:
            # Remove all callbacks for this keyword
            del self._keywords[keyword]
        else:
            # Remove specific callback if registered
            try:
                self._keywords[keyword].remove(callback)
                if not self._keywords[keyword]:
                    del self._keywords[keyword]
            except ValueError:
                pass
        self._compiled = False

    def compile(self) -> None:
        """
        Compile the registered keywords into an Aho-Corasick trie with failure links.
        """
        # Initialize the root of the trie
        root = _Node()
        max_len = 0
        # Build the trie: insert each keyword and attach its callbacks
        for kw, callbacks in self._keywords.items():
            max_len = max(max_len, len(kw))
            node = root
            for ch in kw:
                # Create a child node if missing
                node = node.children.setdefault(ch, _Node())
            # At the end of the keyword, record its callbacks
            node.output.append((kw, list(callbacks)))
        # Set failure link of root to itself
        root.fail = root
        # Initialize BFS queue with direct children of root
        queue: List[_Node] = []
        for child in root.children.values():
            child.fail = root
            queue.append(child)
        # Build failure links in BFS order
        while queue:
            current = queue.pop(0)
            for ch, child in current.children.items():
                queue.append(child)
                # Find the failure link for the child
                failure = current.fail
                while failure is not root and ch not in failure.children:
                    failure = failure.fail
                child.fail = failure.children.get(ch, root)
                # Merge output links (keywords) from failure node
                child.output.extend(child.fail.output)
        # Save compiled trie and metadata
        self._root = root
        self._max_len = max_len
        self._compiled = True

    def max_len(self) -> int:
        """Return the maximum keyword length registered."""
        if not self._compiled:
            self.compile()
        return self._max_len
"""
Internal module: Aho–Corasick trie node definition.

Defines the _Node class used by KeywordRegistry to build a multi-pattern
matching automaton with failure links.
"""
from typing import Callable, Dict, List, Optional, Tuple
from .context import ActionContext
from .types import ActionDecision

class _Node:
    __slots__ = ('children', 'fail', 'output')  # optimize memory for node attributes

    def __init__(self):
        # Mapping from character to child node
        self.children: Dict[str, _Node] = {}
        # Failure link in the Aho–Corasick automaton
        self.fail: Optional[_Node] = None
        # List of (keyword, callbacks) tuples that end at this node
        self.output: List[Tuple[str, List[Callable[[ActionContext], ActionDecision]]]] = []
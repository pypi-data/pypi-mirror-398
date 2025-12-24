"""
Integration layer exposing the @llm_stream_processor decorator for token generators.
"""
import inspect

from ..engine.processor import StreamProcessor
from ..engine.exceptions import StreamHalted

def _repack(chars, mode):
    """
    Repack a list of characters into the desired yield mode.
    """
    if mode == 'char':
        for c in chars:
            yield c
    elif mode == 'token':
        yield ''.join(chars)
    elif mode.startswith('chunk:'):
        try:
            size = int(mode.split(':', 1)[1])
        except (IndexError, ValueError):
            raise ValueError(f"Invalid chunk size in mode '{mode}'")
        for i in range(0, len(chars), size):
            yield ''.join(chars[i:i+size])
    else:
        raise ValueError(f"Unknown yield mode '{mode}'")

def llm_stream_processor(registry, *, yield_mode='token', record_history=True):
    """
    Decorator to apply LLM stream processing to a token generator (sync or async).

    Usage:
        @llm_stream_processor(registry, yield_mode='token')
        def gen():
            yield '...'
    """
    def decorator(fn):  # noqa: C901
        if inspect.isasyncgenfunction(fn):
            async def async_wrap(*args, **kwargs):
                sp = StreamProcessor(registry, record_history=record_history)
                # TOKEN mode: yield one string per input token
                if yield_mode == 'token':
                    async for token in fn(*args, **kwargs):
                        out_chars: list = []
                        for ch in token:
                            try:
                                out_chars.extend(sp.process(ch))
                            except StreamHalted:
                                out_chars.extend(sp.flush())
                                if out_chars:
                                    yield ''.join(out_chars)
                                return
                        out_chars.extend(sp.flush())
                        yield ''.join(out_chars)
                    return
                # CHAR or CHUNK modes
                try:
                    async for token in fn(*args, **kwargs):
                        out_chars = []
                        try:
                            for ch in token:
                                out_chars.extend(sp.process(ch))
                        except StreamHalted:
                            return
                        for item in _repack(out_chars, yield_mode):
                            yield item
                    # Final flush
                    rem = sp.flush()
                    if rem:
                        for item in _repack(rem, yield_mode):
                            yield item
                except StreamHalted:
                    return
            async_wrap.registry = registry
            return async_wrap
        elif inspect.isgeneratorfunction(fn):
            def sync_wrap(*args, **kwargs):
                sp = StreamProcessor(registry, record_history=record_history)
                if yield_mode == 'token':
                    for token in fn(*args, **kwargs):
                        out_chars: list = []
                        for ch in token:
                            try:
                                out_chars.extend(sp.process(ch))
                            except StreamHalted:
                                out_chars.extend(sp.flush())
                                if out_chars:
                                    yield ''.join(out_chars)
                                return
                        out_chars.extend(sp.flush())
                        yield ''.join(out_chars)
                    return
                for token in fn(*args, **kwargs):
                    out_chars = []
                    try:
                        for ch in token:
                            out_chars.extend(sp.process(ch))
                    except StreamHalted:
                        return
                    for item in _repack(out_chars, yield_mode):
                        yield item
                rem = sp.flush()
                if rem:
                    for item in _repack(rem, yield_mode):
                        yield item
            sync_wrap.registry = registry
            return sync_wrap
        else:
            raise TypeError("llm_stream_processor decorator can only wrap generators")
    return decorator
"""
Defines exceptions used by llm_stream_processor engine.

StreamHalted signals immediate termination of the stream processing.
"""
class StreamHalted(Exception):
    """
    Raised to signal that the stream processing should be aborted immediately.
    """
    pass
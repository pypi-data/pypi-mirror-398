"""
Vision Stream Toolkit - Pythonic video streaming made simple.

Turn messy OpenCV video loops into clean Python generators.
"""

from .stream import VideoStream, stream, FrameData, StreamStats

__version__ = "0.1.0"
__all__ = ["VideoStream", "stream", "FrameData", "StreamStats", "__version__"]

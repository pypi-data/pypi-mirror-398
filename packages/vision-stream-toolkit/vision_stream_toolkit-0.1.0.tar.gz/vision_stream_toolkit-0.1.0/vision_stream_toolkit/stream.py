"""
Core video streaming functionality with threaded frame capture.
"""

import atexit
import threading
import time
import weakref
from collections import deque
from queue import Queue, Empty
from typing import Generator, Union, Optional, Callable, Deque
from dataclasses import dataclass

import cv2
import numpy as np

# Track all active streams for cleanup on exit
_active_streams: weakref.WeakSet = weakref.WeakSet()


def _cleanup_all_streams():
    """Clean up all active streams on program exit."""
    for stream in list(_active_streams):
        try:
            stream.stop()
        except Exception:
            pass
    cv2.destroyAllWindows()


# Register cleanup on normal exit
atexit.register(_cleanup_all_streams)


@dataclass
class FrameData:
    """Container for frame data with metadata."""
    frame: np.ndarray
    timestamp: float
    frame_number: int


@dataclass
class StreamStats:
    """
    Real-time statistics for video stream performance.

    Attributes:
        fps_capture: Actual frames per second being captured
        fps_processing: Frames per second being processed/consumed
        frames_captured: Total frames captured from source
        frames_processed: Total frames yielded to user
        frames_dropped: Total frames dropped (buffer full)
        frames_skipped: Total frames skipped (skip_frames setting)
        latency_ms: Current capture-to-process latency in milliseconds
        uptime_seconds: Total seconds stream has been running
        reconnect_count: Number of times stream has reconnected
        is_connected: Whether stream is currently connected
    """
    fps_capture: float = 0.0
    fps_processing: float = 0.0
    frames_captured: int = 0
    frames_processed: int = 0
    frames_dropped: int = 0
    frames_skipped: int = 0
    latency_ms: float = 0.0
    uptime_seconds: float = 0.0
    reconnect_count: int = 0
    is_connected: bool = False

    def __str__(self) -> str:
        return (
            f"StreamStats(fps_cap={self.fps_capture:.1f}, "
            f"fps_proc={self.fps_processing:.1f}, "
            f"dropped={self.frames_dropped}, "
            f"latency={self.latency_ms:.1f}ms)"
        )


class _StatsTracker:
    """Internal class for tracking stream statistics."""

    def __init__(self, window_size: int = 30):
        self.window_size = window_size
        self._capture_times: Deque[float] = deque(maxlen=window_size)
        self._process_times: Deque[float] = deque(maxlen=window_size)
        self._frames_captured = 0
        self._frames_processed = 0
        self._frames_dropped = 0
        self._frames_skipped = 0
        self._reconnect_count = 0
        self._start_time = time.time()
        self._last_capture_time = 0.0
        self._is_connected = False
        self._lock = threading.Lock()

    def record_capture(self) -> None:
        """Record a frame capture event."""
        now = time.time()
        with self._lock:
            self._capture_times.append(now)
            self._frames_captured += 1
            self._last_capture_time = now

    def record_process(self) -> None:
        """Record a frame process/yield event."""
        with self._lock:
            self._process_times.append(time.time())
            self._frames_processed += 1

    def record_drop(self) -> None:
        """Record a dropped frame."""
        with self._lock:
            self._frames_dropped += 1

    def record_skip(self) -> None:
        """Record a skipped frame."""
        with self._lock:
            self._frames_skipped += 1

    def record_reconnect(self) -> None:
        """Record a reconnection event."""
        with self._lock:
            self._reconnect_count += 1

    def set_connected(self, connected: bool) -> None:
        """Set connection status."""
        with self._lock:
            self._is_connected = connected

    def get_stats(self) -> StreamStats:
        """Get current statistics snapshot."""
        with self._lock:
            now = time.time()

            # Calculate capture FPS from recent captures
            fps_capture = 0.0
            if len(self._capture_times) >= 2:
                time_span = self._capture_times[-1] - self._capture_times[0]
                if time_span > 0:
                    fps_capture = (len(self._capture_times) - 1) / time_span

            # Calculate processing FPS
            fps_processing = 0.0
            if len(self._process_times) >= 2:
                time_span = self._process_times[-1] - self._process_times[0]
                if time_span > 0:
                    fps_processing = (len(self._process_times) - 1) / time_span

            # Calculate latency (time since last capture)
            latency_ms = 0.0
            if self._last_capture_time > 0:
                latency_ms = (now - self._last_capture_time) * 1000

            return StreamStats(
                fps_capture=fps_capture,
                fps_processing=fps_processing,
                frames_captured=self._frames_captured,
                frames_processed=self._frames_processed,
                frames_dropped=self._frames_dropped,
                frames_skipped=self._frames_skipped,
                latency_ms=latency_ms,
                uptime_seconds=now - self._start_time,
                reconnect_count=self._reconnect_count,
                is_connected=self._is_connected,
            )

    def reset(self) -> None:
        """Reset all statistics."""
        with self._lock:
            self._capture_times.clear()
            self._process_times.clear()
            self._frames_captured = 0
            self._frames_processed = 0
            self._frames_dropped = 0
            self._frames_skipped = 0
            self._start_time = time.time()
            self._last_capture_time = 0.0


class VideoStream:
    """
    A threaded video stream wrapper that provides a clean generator interface.

    Handles frame capture in a background thread, allowing your processing
    logic to run without blocking frame acquisition.

    Args:
        source: Camera index (int) or video file path (str)
        queue_size: Max frames to buffer (default: 128)
        fps_limit: Optional FPS cap (None = no limit)
        transform: Optional function to apply to each frame
        drop_frames: If True (default), drops old frames when queue is full
                     to keep buffer fresh. Set to False for video files
                     where you need every frame.
        skip_frames: Process every Nth frame (default: 1 = no skip).
                     Set to 3 to process every 3rd frame, reducing load.
        auto_reconnect: If True, automatically reconnect on disconnect (default: False)
        reconnect_delay: Seconds to wait between reconnection attempts (default: 1.0)
        max_reconnect_attempts: Max reconnection attempts, 0 = infinite (default: 5)
        on_connect: Callback function called when stream connects
        on_disconnect: Callback function called when stream disconnects
        on_reconnect: Callback function called on successful reconnection

    Example:
        >>> with VideoStream(source=0) as stream:
        ...     for frame in stream:
        ...         cv2.imshow("Feed", frame)
        ...         if cv2.waitKey(1) & 0xFF == ord('q'):
        ...             break
    """

    def __init__(
        self,
        source: Union[int, str] = 0,
        queue_size: int = 128,
        fps_limit: Optional[float] = None,
        transform: Optional[Callable[[np.ndarray], np.ndarray]] = None,
        drop_frames: bool = True,
        skip_frames: int = 1,
        auto_reconnect: bool = False,
        reconnect_delay: float = 1.0,
        max_reconnect_attempts: int = 5,
        on_connect: Optional[Callable[[], None]] = None,
        on_disconnect: Optional[Callable[[], None]] = None,
        on_reconnect: Optional[Callable[[int], None]] = None,
    ):
        self.source = source
        self.queue_size = queue_size
        self.fps_limit = fps_limit
        self.transform = transform
        self.drop_frames = drop_frames
        self.skip_frames = max(1, skip_frames)
        self.auto_reconnect = auto_reconnect
        self.reconnect_delay = reconnect_delay
        self.max_reconnect_attempts = max_reconnect_attempts

        # Callbacks
        self._on_connect = on_connect
        self._on_disconnect = on_disconnect
        self._on_reconnect = on_reconnect

        self._cap: Optional[cv2.VideoCapture] = None
        self._frame_queue: Queue = Queue(maxsize=queue_size)
        self._thread: Optional[threading.Thread] = None
        self._stopped = threading.Event()
        self._started = False
        self._frame_count = 0
        self._start_time = 0.0

        # Statistics tracking
        self._stats = _StatsTracker()

    def start(self) -> "VideoStream":
        """Start the video capture thread."""
        if self._started:
            return self

        self._cap = cv2.VideoCapture(self.source)
        if not self._cap.isOpened():
            raise RuntimeError(f"Failed to open video source: {self.source}")

        self._stopped.clear()
        self._start_time = time.time()
        self._frame_count = 0
        self._stats.reset()
        self._stats.set_connected(True)

        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        self._started = True

        # Register for auto-cleanup on exit
        _active_streams.add(self)

        # Call on_connect callback
        if self._on_connect:
            try:
                self._on_connect()
            except Exception:
                pass

        return self

    def stop(self) -> None:
        """Stop the video capture thread and release resources."""
        self._stopped.set()
        self._stats.set_connected(False)

        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

        if self._cap is not None:
            self._cap.release()
            self._cap = None

        self._started = False

        # Clear remaining frames from queue
        while not self._frame_queue.empty():
            try:
                self._frame_queue.get_nowait()
            except Empty:
                break

    def _try_reconnect(self) -> bool:
        """Attempt to reconnect to the video source."""
        if not self.auto_reconnect:
            return False

        attempts = 0
        while not self._stopped.is_set():
            if self.max_reconnect_attempts > 0 and attempts >= self.max_reconnect_attempts:
                return False

            attempts += 1
            self._stats.record_reconnect()

            # Release existing capture
            if self._cap is not None:
                self._cap.release()

            time.sleep(self.reconnect_delay)

            # Try to reconnect
            self._cap = cv2.VideoCapture(self.source)
            if self._cap.isOpened():
                self._stats.set_connected(True)

                # Call on_reconnect callback
                if self._on_reconnect:
                    try:
                        self._on_reconnect(attempts)
                    except Exception:
                        pass

                return True

        return False

    def _capture_loop(self) -> None:
        """Background thread that continuously captures frames."""
        frame_interval = 1.0 / self.fps_limit if self.fps_limit else 0
        last_frame_time = 0.0
        raw_frame_count = 0

        while not self._stopped.is_set():
            if self._cap is None:
                break

            # FPS limiting
            if self.fps_limit:
                current_time = time.time()
                elapsed = current_time - last_frame_time
                if elapsed < frame_interval:
                    time.sleep(frame_interval - elapsed)
                last_frame_time = time.time()

            ret, frame = self._cap.read()

            if not ret:
                self._stats.set_connected(False)

                # Call on_disconnect callback
                if self._on_disconnect:
                    try:
                        self._on_disconnect()
                    except Exception:
                        pass

                # Try to reconnect
                if self._try_reconnect():
                    continue
                else:
                    self._stopped.set()
                    break

            raw_frame_count += 1
            self._stats.record_capture()

            # Skip frames: only process every Nth frame
            if raw_frame_count % self.skip_frames != 0:
                self._stats.record_skip()
                continue

            # Apply transform if provided
            if self.transform is not None:
                frame = self.transform(frame)

            self._frame_count += 1
            timestamp = time.time() - self._start_time

            frame_data = FrameData(
                frame=frame,
                timestamp=timestamp,
                frame_number=self._frame_count
            )

            if self.drop_frames:
                # Real-time mode: drop oldest frame if queue is full
                if self._frame_queue.full():
                    try:
                        self._frame_queue.get_nowait()
                        self._stats.record_drop()
                    except Empty:
                        pass
                try:
                    self._frame_queue.put_nowait(frame_data)
                except Exception:
                    self._stats.record_drop()
            else:
                # Offline mode: block until queue has space (keeps ALL frames)
                self._frame_queue.put(frame_data)

    def read(self, timeout: float = 1.0) -> Optional[FrameData]:
        """
        Read a single frame from the stream.

        Args:
            timeout: Max seconds to wait for a frame

        Returns:
            FrameData or None if no frame available
        """
        if not self._started:
            self.start()

        try:
            frame_data = self._frame_queue.get(timeout=timeout)
            self._stats.record_process()
            return frame_data
        except Empty:
            return None

    def frames(self, include_metadata: bool = False) -> Generator:
        """
        Generator that yields frames from the video stream.

        Args:
            include_metadata: If True, yields FrameData objects.
                              If False, yields raw numpy arrays.
        """
        if not self._started:
            self.start()

        while not self._stopped.is_set() or not self._frame_queue.empty():
            try:
                frame_data = self._frame_queue.get(timeout=0.1)
                self._stats.record_process()
                if include_metadata:
                    yield frame_data
                else:
                    yield frame_data.frame
            except Empty:
                if self._stopped.is_set():
                    break
                continue

    @property
    def stats(self) -> StreamStats:
        """Get current stream statistics."""
        return self._stats.get_stats()

    def print_stats(self) -> None:
        """Print current statistics to console."""
        s = self.stats
        print(f"\n{'='*50}")
        print(f"Stream Statistics")
        print(f"{'='*50}")
        print(f"  Capture FPS:     {s.fps_capture:.1f}")
        print(f"  Processing FPS:  {s.fps_processing:.1f}")
        print(f"  Frames captured: {s.frames_captured}")
        print(f"  Frames processed:{s.frames_processed}")
        print(f"  Frames dropped:  {s.frames_dropped}")
        print(f"  Frames skipped:  {s.frames_skipped}")
        print(f"  Latency:         {s.latency_ms:.1f}ms")
        print(f"  Uptime:          {s.uptime_seconds:.1f}s")
        print(f"  Reconnects:      {s.reconnect_count}")
        print(f"  Connected:       {s.is_connected}")
        print(f"{'='*50}\n")

    def __iter__(self) -> Generator[np.ndarray, None, None]:
        """Iterate over frames as numpy arrays."""
        return self.frames(include_metadata=False)

    def __enter__(self) -> "VideoStream":
        """Context manager entry."""
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.stop()
        cv2.destroyAllWindows()

    @property
    def fps(self) -> float:
        """Get the source video's FPS (if available)."""
        if self._cap is not None:
            return self._cap.get(cv2.CAP_PROP_FPS)
        return 0.0

    @property
    def frame_size(self) -> tuple:
        """Get frame dimensions as (width, height)."""
        if self._cap is not None:
            w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            return (w, h)
        return (0, 0)

    @property
    def is_running(self) -> bool:
        """Check if the stream is currently running."""
        return self._started and not self._stopped.is_set()

    @property
    def is_connected(self) -> bool:
        """Check if the stream is currently connected to source."""
        return self._stats.get_stats().is_connected


def stream(
    source: Union[int, str] = 0,
    queue_size: int = 128,
    fps_limit: Optional[float] = None,
    transform: Optional[Callable[[np.ndarray], np.ndarray]] = None,
    drop_frames: bool = True,
    skip_frames: int = 1,
    auto_reconnect: bool = False,
    reconnect_delay: float = 1.0,
    max_reconnect_attempts: int = 5,
) -> Generator[np.ndarray, None, None]:
    """
    Convenience function to stream video frames as a generator.

    This is the simplest way to iterate over video frames:

        for frame in stream(source=0):
            # Your AI logic here
            cv2.imshow("Feed", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    Args:
        source: Camera index (int) or video file path (str)
        queue_size: Max frames to buffer (default: 128)
        fps_limit: Optional FPS cap (None = no limit)
        transform: Optional function to apply to each frame
        drop_frames: If True (default), drops old frames to stay real-time.
                     Set to False for video files to process ALL frames.
        skip_frames: Process every Nth frame (default: 1 = no skip).
                     Set to 3 to process every 3rd frame.
        auto_reconnect: If True, automatically reconnect on disconnect.
        reconnect_delay: Seconds to wait between reconnection attempts.
        max_reconnect_attempts: Max reconnection attempts, 0 = infinite.

    Yields:
        numpy.ndarray: Video frames in BGR format
    """
    video_stream = VideoStream(
        source=source,
        queue_size=queue_size,
        fps_limit=fps_limit,
        transform=transform,
        drop_frames=drop_frames,
        skip_frames=skip_frames,
        auto_reconnect=auto_reconnect,
        reconnect_delay=reconnect_delay,
        max_reconnect_attempts=max_reconnect_attempts,
    )

    try:
        video_stream.start()
        yield from video_stream.frames(include_metadata=False)
    finally:
        video_stream.stop()
        cv2.destroyAllWindows()

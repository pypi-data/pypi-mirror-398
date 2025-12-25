# Vision Stream Toolkit

**Pythonic video streaming made simple.** Turn messy OpenCV video loops into clean Python generators.

---

## The Problem

Working with video in Python (OpenCV) is painful. You need 40+ lines of boilerplate just to handle threading, frame drops, and cleanup properly.

### Traditional OpenCV Approach

```python
import cv2
import threading
from queue import Queue, Empty

# ========== 40+ LINES OF BOILERPLATE ==========

class ThreadedCamera:
    def __init__(self, src=0):
        self.cap = cv2.VideoCapture(src)
        self.q = Queue(maxsize=128)
        self.stopped = False

    def start(self):
        t = threading.Thread(target=self._reader)
        t.daemon = True
        t.start()
        return self

    def _reader(self):
        while not self.stopped:
            ret, frame = self.cap.read()
            if not ret:
                self.stopped = True
                break
            if self.q.full():
                try:
                    self.q.get_nowait()
                except Empty:
                    pass
            self.q.put(frame)

    def read(self):
        return self.q.get(timeout=1.0)

    def stop(self):
        self.stopped = True
        self.cap.release()

# ========== FINALLY, YOUR ACTUAL CODE ==========

cam = ThreadedCamera(0)
cam.start()

try:
    while True:
        try:
            frame = cam.read()
        except Empty:
            break

        # Your AI inference here
        results = model.predict(frame)

        cv2.imshow("Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    cam.stop()
    cv2.destroyAllWindows()
```

### With Vision Stream Toolkit

```python
from vision_stream_toolkit import stream
import cv2

for frame in stream(source=0):
    # Your AI inference here
    results = model.predict(frame)

    cv2.imshow("Detection", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
```

**That's it.** 6 lines instead of 50+.

---

## Why Use Vision Stream Toolkit?

| Problem | Traditional OpenCV | Vision Stream Toolkit |
|---------|-------------------|----------------------|
| **Boilerplate code** | 40+ lines for threading | 1 line: `stream(source=0)` |
| **Frame lag** | Manual queue management | Automatic buffer with smart dropping |
| **Resource cleanup** | `try/finally` everywhere | Automatic via context manager + atexit |
| **Frame skipping** | Implement yourself | Built-in `skip_frames` parameter |
| **FPS control** | Manual sleep calculations | Built-in `fps_limit` parameter |
| **Transforms** | Separate processing loop | Built-in `transform` parameter |
| **Crash safety** | Resources often leak | Auto-cleanup on exit/crash |
| **Code style** | `while True` loops | Pythonic generators |
| **Stream monitoring** | Build your own metrics | Built-in `stats` with FPS, drops, latency |
| **Connection drops** | Manual reconnect logic | `auto_reconnect=True` handles it |
| **Event handling** | Polling for state changes | Callbacks: `on_connect`, `on_disconnect` |

---

## Installation

```bash
pip install vision-stream-toolkit
```

---

## Quick Start

### Basic Webcam Stream

```python
from vision_stream_toolkit import stream

for frame in stream(source=0):
    cv2.imshow("Webcam", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
```

### From Video File

```python
for frame in stream(source="video.mp4", drop_frames=False):
    process_frame(frame)
```

### RTSP / IP Camera

```python
for frame in stream(source="rtsp://192.168.1.100:554/stream"):
    process_frame(frame)
```

---

## Features

### 1. Threaded Capture (No Frame Lag)

The camera runs in a background thread, so your slow AI model never blocks frame acquisition.

```
Without threading:
[Capture] → [Process 200ms] → [Capture] → [Process 200ms]
                               ↑ Camera blocked, frames lost!

With Vision Stream Toolkit:
[Capture Thread] → [Queue] → [Your Code]
     ↓                            ↓
  Continuous                 Process when ready
  30+ FPS                    Always fresh frames
```

### 2. Smart Frame Dropping (`drop_frames`)

Control whether to drop old frames (real-time) or keep all frames (offline processing).

```python
# Real-time mode (default) - always get fresh frames
for frame in stream(source=0, drop_frames=True):
    slow_model.predict(frame)  # Old frames dropped, always current

# Offline mode - process EVERY frame
for frame in stream(source="video.mp4", drop_frames=False):
    slow_model.predict(frame)  # No frames lost, takes longer
```

**Visual explanation:**

```
Camera: 30 FPS → [1][2][3][4][5][6][7][8][9][10]...
Model:  5 FPS (200ms per inference)

drop_frames=True (Real-time):
  Model sees: [1]...[4]...[7]...[10]  → Always fresh, frames 2,3,5,6,8,9 dropped

drop_frames=False (Offline):
  Model sees: [1][2][3][4][5][6][7][8][9][10]  → All frames, 6x slower than real-time
```

### 3. Frame Skipping (`skip_frames`)

Intentionally process every Nth frame to reduce compute load.

```python
# Process every 3rd frame (10 FPS from 30 FPS source)
for frame in stream(source=0, skip_frames=3):
    expensive_model.predict(frame)

# Process every 10th frame (for thumbnails, time-lapse)
for frame in stream(source="video.mp4", skip_frames=10):
    save_thumbnail(frame)
```

**Visual explanation:**

```
Source: [1][2][3][4][5][6][7][8][9][10][11][12]...

skip_frames=1:  [1][2][3][4][5][6][7][8][9][10][11][12]  (all frames)
skip_frames=3:  [3]      [6]      [9]         [12]       (every 3rd)
skip_frames=5:  [5]               [10]                   (every 5th)
```

### 4. FPS Limiting (`fps_limit`)

Cap the frame rate to reduce CPU/GPU usage.

```python
# Limit to 15 FPS (saves CPU when you don't need 30+ FPS)
for frame in stream(source=0, fps_limit=15):
    process(frame)
```

### 5. Transform Pipeline (`transform`)

Apply transformations before frames reach your code.

```python
def preprocess(frame):
    frame = cv2.resize(frame, (640, 480))
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return frame

for frame in stream(source=0, transform=preprocess):
    # Frames already resized and converted to RGB
    model.predict(frame)
```

### 6. Frame Metadata

Access timestamps and frame numbers for analysis.

```python
from vision_stream_toolkit import VideoStream

with VideoStream(source=0) as vs:
    for frame_data in vs.frames(include_metadata=True):
        print(f"Frame #{frame_data.frame_number}")
        print(f"Timestamp: {frame_data.timestamp:.2f}s")
        process(frame_data.frame)
```

### 7. Auto-Cleanup

Resources are automatically released on:
- Normal exit
- Exceptions/crashes
- Ctrl+C (KeyboardInterrupt)
- Context manager exit

```python
# No try/finally needed!
for frame in stream(source=0):
    if some_condition:
        raise Exception("Oops!")  # Camera still released properly
```

### 8. Real-Time Statistics (`stats`)

Monitor stream performance with detailed metrics.

```python
from vision_stream_toolkit import VideoStream

with VideoStream(source=0) as vs:
    for i, frame in enumerate(vs):
        if i % 100 == 0:  # Print stats every 100 frames
            stats = vs.stats
            print(f"Capture FPS: {stats.fps_capture:.1f}")
            print(f"Process FPS: {stats.fps_processing:.1f}")
            print(f"Dropped: {stats.frames_dropped}")
            print(f"Latency: {stats.latency_ms:.1f}ms")

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Print final statistics
    vs.print_stats()
```

**Available Statistics:**

| Metric | Description |
|--------|-------------|
| `fps_capture` | Actual frames per second being captured |
| `fps_processing` | Frames per second being consumed |
| `frames_captured` | Total frames captured from source |
| `frames_processed` | Total frames yielded to user |
| `frames_dropped` | Frames dropped (buffer full) |
| `frames_skipped` | Frames skipped (`skip_frames` setting) |
| `latency_ms` | Capture-to-process latency in milliseconds |
| `uptime_seconds` | Total seconds stream has been running |
| `reconnect_count` | Number of reconnection attempts |
| `is_connected` | Current connection status |

### 9. Auto-Reconnect (`auto_reconnect`)

Automatically reconnect when RTSP streams or cameras disconnect.

```python
# RTSP stream with auto-reconnect
for frame in stream(
    source="rtsp://192.168.1.100:554/stream",
    auto_reconnect=True,
    reconnect_delay=2.0,        # Wait 2s between attempts
    max_reconnect_attempts=10,  # Try 10 times (0 = infinite)
):
    process(frame)
```

**With Callbacks:**

```python
def on_connect():
    print("Stream connected!")

def on_disconnect():
    print("Stream disconnected! Attempting reconnect...")

def on_reconnect(attempt):
    print(f"Reconnected after {attempt} attempts!")

vs = VideoStream(
    source="rtsp://camera.local/stream",
    auto_reconnect=True,
    max_reconnect_attempts=0,  # Infinite retries
    on_connect=on_connect,
    on_disconnect=on_disconnect,
    on_reconnect=on_reconnect,
)

with vs:
    for frame in vs:
        process(frame)
```

---

## API Reference

### `stream()` - Simple Generator Function

```python
from vision_stream_toolkit import stream

for frame in stream(
    source=0,                    # Camera index or video path
    queue_size=128,              # Frame buffer size
    fps_limit=None,              # Optional FPS cap
    transform=None,              # Optional transform function
    drop_frames=True,            # Drop old frames when buffer full
    skip_frames=1,               # Process every Nth frame
    auto_reconnect=False,        # Auto-reconnect on disconnect
    reconnect_delay=1.0,         # Delay between reconnect attempts
    max_reconnect_attempts=5,    # Max reconnect attempts (0 = infinite)
):
    process(frame)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source` | `int \| str` | `0` | Camera index, video file path, or RTSP URL |
| `queue_size` | `int` | `128` | Maximum frames to buffer |
| `fps_limit` | `float \| None` | `None` | Cap frame rate (None = unlimited) |
| `transform` | `Callable \| None` | `None` | Function to transform each frame |
| `drop_frames` | `bool` | `True` | Drop old frames to stay real-time |
| `skip_frames` | `int` | `1` | Process every Nth frame (1 = all) |
| `auto_reconnect` | `bool` | `False` | Auto-reconnect on disconnect |
| `reconnect_delay` | `float` | `1.0` | Seconds between reconnect attempts |
| `max_reconnect_attempts` | `int` | `5` | Max attempts (0 = infinite) |

### `VideoStream` - Full Control Class

```python
from vision_stream_toolkit import VideoStream

with VideoStream(source=0) as vs:
    print(f"FPS: {vs.fps}")
    print(f"Size: {vs.frame_size}")
    print(f"Running: {vs.is_running}")

    for frame in vs:
        process(frame)
```

**Methods:**

| Method | Description |
|--------|-------------|
| `start()` | Start the capture thread |
| `stop()` | Stop and release resources |
| `read(timeout=1.0)` | Read a single frame |
| `frames(include_metadata=False)` | Generator for frames |
| `print_stats()` | Print current statistics to console |

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `fps` | `float` | Source video FPS |
| `frame_size` | `tuple` | Frame dimensions (width, height) |
| `is_running` | `bool` | Whether stream is active |
| `is_connected` | `bool` | Whether stream is connected to source |
| `stats` | `StreamStats` | Current performance statistics |

### `FrameData` - Frame Container

```python
@dataclass
class FrameData:
    frame: np.ndarray    # The video frame (BGR)
    timestamp: float     # Seconds since stream start
    frame_number: int    # Sequential frame count
```

### `StreamStats` - Performance Metrics

```python
@dataclass
class StreamStats:
    fps_capture: float       # Capture FPS
    fps_processing: float    # Processing FPS
    frames_captured: int     # Total captured
    frames_processed: int    # Total processed
    frames_dropped: int      # Dropped frames
    frames_skipped: int      # Skipped frames
    latency_ms: float        # Current latency
    uptime_seconds: float    # Stream uptime
    reconnect_count: int     # Reconnection count
    is_connected: bool       # Connection status
```

---

## Parameter Reference (Detailed)

### `source` - Video Source

Specifies where to capture video from. Accepts camera index, file path, or RTSP URL.

```python
# Webcam (default camera)
stream(source=0)

# Secondary camera
stream(source=1)

# Video file
stream(source="/path/to/video.mp4")
stream(source="recording.avi")

# RTSP stream (IP camera)
stream(source="rtsp://192.168.1.100:554/stream")
stream(source="rtsp://admin:password@camera.local/live")

# HTTP stream
stream(source="http://camera.local/video.mjpg")
```

---

### `queue_size` - Frame Buffer Size

Controls how many frames are buffered between capture and processing. Larger buffers handle processing spikes but use more memory.

```python
# Small buffer (low memory, may drop frames if processing is slow)
stream(source=0, queue_size=16)

# Default buffer (balanced)
stream(source=0, queue_size=128)

# Large buffer (high memory, handles processing spikes)
stream(source=0, queue_size=512)
```

**When to adjust:**

| Scenario | Recommended `queue_size` |
|----------|-------------------------|
| Low memory device (Raspberry Pi) | `16-32` |
| Normal desktop | `128` (default) |
| Bursty processing (batch inference) | `256-512` |
| Video file processing | `64-128` |

---

### `fps_limit` - Frame Rate Cap

Limits the capture frame rate to reduce CPU/GPU usage. Set to `None` for maximum FPS.

```python
# No limit (capture as fast as possible)
stream(source=0, fps_limit=None)

# Limit to 30 FPS
stream(source=0, fps_limit=30)

# Limit to 15 FPS (saves CPU for slow models)
stream(source=0, fps_limit=15)

# Limit to 1 FPS (time-lapse, periodic capture)
stream(source=0, fps_limit=1)
```

**Example: Reduce CPU for lightweight tasks**

```python
# Only need 10 FPS for motion detection
for frame in stream(source=0, fps_limit=10):
    if detect_motion(frame):
        alert()
```

---

### `transform` - Frame Preprocessing

Apply a function to every frame before it reaches your code. Runs in the capture thread for efficiency.

```python
import cv2

# Resize frames
def resize_frame(frame):
    return cv2.resize(frame, (640, 480))

for frame in stream(source=0, transform=resize_frame):
    process(frame)  # Already 640x480
```

```python
# Convert to RGB (for ML models)
def to_rgb(frame):
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

for frame in stream(source=0, transform=to_rgb):
    model.predict(frame)  # RGB format
```

```python
# Chain multiple transforms
def preprocess(frame):
    frame = cv2.resize(frame, (224, 224))           # Resize
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # BGR to RGB
    frame = frame / 255.0                            # Normalize
    return frame

for frame in stream(source=0, transform=preprocess):
    model.predict(frame)
```

```python
# Crop region of interest
def crop_center(frame):
    h, w = frame.shape[:2]
    return frame[h//4:3*h//4, w//4:3*w//4]

for frame in stream(source=0, transform=crop_center):
    process(frame)  # Center 50% of frame
```

---

### `drop_frames` - Buffer Overflow Strategy

Controls what happens when the frame buffer is full (processing is slower than capture).

```python
# Real-time mode (default): Drop old frames, always get fresh ones
stream(source=0, drop_frames=True)

# Offline mode: Keep ALL frames, block capture if buffer full
stream(source="video.mp4", drop_frames=False)
```

**Visual comparison:**

```
Camera: 30 FPS, Model: 5 FPS

drop_frames=True:
  Buffer: [new][new][new] → Always fresh, older frames discarded
  Result: Real-time, but only ~17% of frames processed

drop_frames=False:
  Buffer: [1][2][3]...[waiting] → Keeps all, capture waits
  Result: All frames processed, but 6x slower than real-time
```

**When to use each:**

| Use Case | `drop_frames` |
|----------|---------------|
| Live webcam | `True` (default) |
| Security camera | `True` |
| Robotics | `True` |
| Video file analysis | `False` |
| Dataset creation | `False` |
| Frame extraction | `False` |

---

### `skip_frames` - Intentional Frame Skipping

Process only every Nth frame to reduce compute load. Unlike `drop_frames`, this is intentional and predictable.

```python
# Process all frames (default)
stream(source=0, skip_frames=1)

# Process every 2nd frame (15 FPS from 30 FPS source)
stream(source=0, skip_frames=2)

# Process every 5th frame (6 FPS from 30 FPS source)
stream(source=0, skip_frames=5)

# Process every 30th frame (1 FPS from 30 FPS source)
stream(source=0, skip_frames=30)
```

**Example: Reduce GPU load for heavy model**

```python
# YOLOv8 is slow, only run on every 3rd frame
for frame in stream(source=0, skip_frames=3):
    detections = yolo_model.predict(frame)
    draw_boxes(frame, detections)
```

**Example: Create thumbnails**

```python
# Extract 1 frame per second from 30 FPS video
for i, frame in enumerate(stream(source="video.mp4", skip_frames=30, drop_frames=False)):
    cv2.imwrite(f"thumbnail_{i:04d}.jpg", frame)
```

---

### `auto_reconnect` - Automatic Reconnection

Automatically attempt to reconnect when the stream disconnects (camera unplugged, network drop, etc.).

```python
# No reconnection (default): Stop on disconnect
stream(source=0, auto_reconnect=False)

# Auto-reconnect: Try to reconnect on failure
stream(source="rtsp://camera/stream", auto_reconnect=True)
```

**Example: 24/7 surveillance camera**

```python
for frame in stream(
    source="rtsp://192.168.1.100/stream",
    auto_reconnect=True,
    reconnect_delay=5.0,
    max_reconnect_attempts=0,  # Infinite retries
):
    record_frame(frame)
```

---

### `reconnect_delay` - Delay Between Reconnection Attempts

How long to wait before attempting to reconnect after a failure.

```python
# Quick reconnect (local camera)
stream(source=0, auto_reconnect=True, reconnect_delay=0.5)

# Moderate delay (network camera)
stream(source="rtsp://...", auto_reconnect=True, reconnect_delay=2.0)

# Slow reconnect (remote server, rate limiting)
stream(source="rtsp://...", auto_reconnect=True, reconnect_delay=10.0)
```

---

### `max_reconnect_attempts` - Maximum Retry Attempts

How many times to try reconnecting before giving up. Set to `0` for infinite retries.

```python
# Try 5 times then stop (default)
stream(source=0, auto_reconnect=True, max_reconnect_attempts=5)

# Try 3 times
stream(source=0, auto_reconnect=True, max_reconnect_attempts=3)

# Never give up (24/7 systems)
stream(source="rtsp://...", auto_reconnect=True, max_reconnect_attempts=0)
```

---

### `on_connect` - Connection Callback

Function called when stream successfully connects.

```python
def handle_connect():
    print("Stream connected!")
    send_notification("Camera online")

vs = VideoStream(
    source="rtsp://camera/stream",
    on_connect=handle_connect,
)
```

---

### `on_disconnect` - Disconnection Callback

Function called when stream disconnects.

```python
def handle_disconnect():
    print("Stream lost!")
    log_event("Camera disconnected")

vs = VideoStream(
    source="rtsp://camera/stream",
    auto_reconnect=True,
    on_disconnect=handle_disconnect,
)
```

---

### `on_reconnect` - Reconnection Callback

Function called when stream successfully reconnects. Receives the attempt number.

```python
def handle_reconnect(attempt_number):
    print(f"Reconnected after {attempt_number} attempts!")
    send_alert(f"Camera back online (took {attempt_number} tries)")

vs = VideoStream(
    source="rtsp://camera/stream",
    auto_reconnect=True,
    on_reconnect=handle_reconnect,
)
```

---

### Complete Example: All Parameters

```python
import cv2
from vision_stream_toolkit import VideoStream

def preprocess(frame):
    """Resize and convert to RGB."""
    frame = cv2.resize(frame, (640, 480))
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

def on_connect():
    print("Connected to camera!")

def on_disconnect():
    print("Lost connection, attempting reconnect...")

def on_reconnect(attempts):
    print(f"Reconnected after {attempts} attempt(s)")

# Full-featured stream configuration
vs = VideoStream(
    source="rtsp://192.168.1.100:554/stream",  # RTSP camera
    queue_size=64,                              # Moderate buffer
    fps_limit=15,                               # Cap at 15 FPS
    transform=preprocess,                       # Resize + RGB
    drop_frames=True,                           # Real-time mode
    skip_frames=2,                              # Every 2nd frame
    auto_reconnect=True,                        # Auto-reconnect
    reconnect_delay=3.0,                        # Wait 3s between attempts
    max_reconnect_attempts=0,                   # Never give up
    on_connect=on_connect,
    on_disconnect=on_disconnect,
    on_reconnect=on_reconnect,
)

with vs:
    for frame in vs:
        # Process frame (already resized, RGB, every 2nd frame)
        results = model.predict(frame)

        # Monitor performance
        if vs.stats.frames_processed % 100 == 0:
            print(f"FPS: {vs.stats.fps_processing:.1f}, Dropped: {vs.stats.frames_dropped}")
```

---

## Real-World Examples

### Object Detection with YOLO

```python
from vision_stream_toolkit import stream
from ultralytics import YOLO
import cv2

model = YOLO("yolov8n.pt")

for frame in stream(source=0, fps_limit=30):
    results = model.predict(frame, verbose=False)
    annotated = results[0].plot()

    cv2.imshow("YOLOv8 Detection", annotated)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
```

### Face Detection with MediaPipe

```python
from vision_stream_toolkit import stream
import mediapipe as mp
import cv2

face_detection = mp.solutions.face_detection.FaceDetection()

for frame in stream(source=0, skip_frames=2):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_detection.process(rgb)

    if results.detections:
        for detection in results.detections:
            # Draw bounding box
            pass

    cv2.imshow("Face Detection", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
```

### Video File Processing

```python
from vision_stream_toolkit import stream

# Process all frames from a video file
frame_count = 0
for frame in stream(source="input.mp4", drop_frames=False):
    # Your processing here
    frame_count += 1

print(f"Processed {frame_count} frames")
```

### Multi-Camera Setup

```python
from vision_stream_toolkit import VideoStream
import cv2

# Open multiple cameras
cam1 = VideoStream(source=0).start()
cam2 = VideoStream(source=1).start()

try:
    while cam1.is_running and cam2.is_running:
        frame1 = cam1.read()
        frame2 = cam2.read()

        if frame1 and frame2:
            combined = cv2.hconcat([frame1.frame, frame2.frame])
            cv2.imshow("Dual Camera", combined)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    cam1.stop()
    cam2.stop()
```

---

## When to Use Each Parameter

| Scenario | Parameters |
|----------|------------|
| Live webcam + fast model | `stream(source=0)` (defaults) |
| Live webcam + slow model | `stream(source=0, skip_frames=3)` |
| Video file analysis | `stream(source="video.mp4", drop_frames=False)` |
| Reduce CPU usage | `stream(source=0, fps_limit=15)` |
| Thumbnail extraction | `stream(source="video.mp4", skip_frames=30, drop_frames=False)` |
| Pre-resize frames | `stream(source=0, transform=resize_fn)` |
| RTSP security camera | `stream(source="rtsp://...", auto_reconnect=True)` |
| Monitor performance | `VideoStream(source=0)` then access `vs.stats` |
| 24/7 surveillance | `stream(source="rtsp://...", auto_reconnect=True, max_reconnect_attempts=0)` |

---

## Comparison Summary

| Metric | Traditional OpenCV | Vision Stream Toolkit |
|--------|-------------------|----------------------|
| Lines of code | 50+ | 6 |
| Threading | Manual | Automatic |
| Queue management | Manual | Automatic |
| Frame dropping | Manual | `drop_frames=True/False` |
| Frame skipping | Manual | `skip_frames=N` |
| FPS limiting | Manual | `fps_limit=N` |
| Transforms | Separate loop | `transform=fn` |
| Cleanup | `try/finally` | Automatic |
| Crash safety | Often leaks | Always cleans up |
| Statistics | Implement yourself | Built-in `stats` property |
| Auto-reconnect | Manual retry logic | `auto_reconnect=True` |
| Event callbacks | Not available | `on_connect`, `on_disconnect` |
| Learning curve | High | Minimal |

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Contributing

Contributions welcome! Please open an issue or PR on GitHub.

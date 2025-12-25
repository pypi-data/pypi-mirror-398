# vrw: A Simple Library for Video Reading and Writing

![PyPI](https://img.shields.io/pypi/v/vrw)

`vrw` is a lightweight Python library for reading and writing video files with slicing support. It provides a simple interface for handling video frames using NumPy arrays and supports multiple backends like OpenCV and PyAV.

---

## Installation
To install `vrw`, use the following command:

```bash
pip install vrw
```

---

## Usage

### Reading Videos
The `VideoReader` class allows you to read video files and access frames with slicing and indexing.

```python
from vrw import VideoReader

# Open a video file
vr = VideoReader("video.mp4")

# Access video properties
print(vr.shape)  # (N, H, W, C): N frames, H height, W width, C channels
print(vr.fps)    # Frames per second
print(vr.dtype)  # Data type of the frames

# Access frames using slicing
print(vr[:, 0].shape)         # (N, W, C): All frames, first row
print(vr[::2, :, -1].shape)   # (N // 2, H, C): Every second frame, last column
print(vr[..., 0].shape)       # (N, H, W): All frames, first channel
print(vr[[1, 3, 3, 7], :42].shape)  # (4, 42, W, C): Specific frames, first 42 rows

# Reading grayscale frames
vr_gray = VideoReader("video.mp4", to_gray=True)
print(vr_gray.shape)  # (N, H, W): Grayscale frames
```

Note that [advanced indexing](https://numpy.org/doc/2.2/user/basics.indexing.html#advanced-indexing) involving the 0th axis has not been implemented yet.

### Writing Videos
The `VideoWriter` class allows you to write video files frame by frame.

#### Writing RGB Frames
```python
from vrw import VideoWriter
import numpy as np

# Write RGB frames to a video file
with VideoWriter("video.mp4", fps=30) as vw:
    for i in range(256):
        im = np.full((256, 256, 3), i, dtype=np.uint8)
        im[..., 0], im[..., 1] = np.mgrid[:256, :256]
        vw.write(im)
```

#### Writing Grayscale Frames
```python
# Write grayscale frames to a video file
with VideoWriter("video.mp4", fps=30) as vw:
    for i in range(256):
        vw.write(np.full((256, 256), i, dtype=np.uint8))
```

#### Using the PyAV Backend
The PyAV backend allows you to use advanced codecs (e.g., `libx264`) for video writing. Ensure that FFmpeg is installed and built with the required codecs.

```python
# Use the PyAV backend with a specific codec
with VideoWriter("video.mp4", fps=30, backend="pyav", codec="libx264") as vw:
    for i in range(256):
        im = np.full((256, 256, 3), i, dtype=np.uint8)
        im[..., 0], im[..., 1] = np.mgrid[:256, :256]
        vw.write(im)
```

---

## Backends
`vrw` supports the following backends
- **OpenCV**: Default backend for reading and writing videos.
- **PyAV**: Alternative backend for advanced codec support (requires FFmpeg built with the necessary codecs).

To specify a backend, use the `backend` parameter  (e.g., `backend="cv2"` or `backend="pyav"`) when creating a `VideoReader` or `VideoWriter` instance.
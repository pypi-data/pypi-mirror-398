from .base import WriterBackend
import cv2
import numpy as np


class Cv2Backend(WriterBackend):
    def __init__(self, filename: str, fps: float, fourcc="mp4v"):
        super().__init__(filename=filename, fps=fps)
        self._fourcc = fourcc
        self._writer = None

    def _init(self, frame_shape):
        if len(frame_shape) not in (2, 3):
            raise ValueError("frame_shape must be (H, W) or (H, W, C)")
        h, w = frame_shape[:2]
        is_color = len(frame_shape) == 3
        self._writer = cv2.VideoWriter(
            self._filename,
            cv2.VideoWriter_fourcc(*self._fourcc),
            self._fps,
            (w, h),
            is_color,
        )

    def write(self, frame: np.ndarray):
        frame = np.asarray(frame)
        if self._writer is None:
            self._init(frame.shape)
        if len(frame.shape) == 3:
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        self._writer.write(frame)
        self._n_frames += 1

    def close(self):
        if self._writer is not None:
            self._writer.release()
            self._writer = None

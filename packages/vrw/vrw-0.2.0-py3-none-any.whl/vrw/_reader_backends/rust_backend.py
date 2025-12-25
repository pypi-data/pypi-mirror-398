from functools import cached_property
from video_reader import PyVideoReader
from .base import ReaderBackend


class RustBackend(ReaderBackend):
    def __init__(self, path: str | bytes, to_gray=False):
        super().__init__(path, to_gray)
        self._reader = PyVideoReader(str(self._path))
        if to_gray:
            self._decode_func = self._reader.decode_gray
        else:
            self._decode_func = self._reader.decode

    def get_frame(self, frame_id: int):
        if frame_id < -self.n_frames or frame_id >= self.n_frames:
            raise IndexError(f"Frame {frame_id} out of range")
        if frame_id < 0:
            frame_id += self.n_frames
        return self._decode_func(frame_id, frame_id + 1, 1)[0]

    @property
    def n_frames(self) -> int:
        return len(self._reader)

    @cached_property
    def fps(self) -> float:
        return self._reader.get_fps()

    @cached_property
    def width(self) -> int:
        return self._reader.get_shape()[2]

    @cached_property
    def height(self) -> int:
        return self._reader.get_shape()[1]

    def close(self):
        del self._reader

    def __del__(self):
        self.close()

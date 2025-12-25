from abc import ABC, abstractmethod
import numpy as np
from os import PathLike


class ReaderBackend(ABC):
    """
    Abstract base class for video reader backends. Methods like
    `iter_frames` have been implemented based on the single-frame
    reading method `get_frame` but can be overridden if there are
    more efficient ways to read multiple frames.

    Parameters
    ----------
    path : str or PathLike
        Path to the video file.
    to_gray : bool
        Whether to convert frames to grayscale.
    """

    def __init__(self, path: str | PathLike, to_gray: bool):
        self._path = str(path)
        self._to_gray = to_gray

    @staticmethod
    def from_name(name: str) -> type["ReaderBackend"]:
        """
        Create a Backend instance from a name.

        Parameters
        ----------
        name : str
            Name of the backend.

        Returns
        -------
        type[ReaderBackend]
            The backend class corresponding to the given name.

        Raises
        ------
        NotImplementedError
            If the backend name is not implemented.
        """
        if name == "cv2":
            from .cv2_backend import Cv2Backend

            return Cv2Backend
        elif name == "rust":
            from .rust_backend import RustBackend

            return RustBackend

        raise NotImplementedError(
            f"Backend '{name}' is not implemented. Available backends: cv2, rust"
        )

    @abstractmethod
    def get_frame(self, frame_id: int) -> np.ndarray:
        """
        Retrieve a single frame by its ID.

        Parameters
        ----------
        frame_id : int
            The ID of the frame to retrieve.

        Returns
        -------
        np.ndarray
            The frame as a NumPy array.
        """
        pass

    def iter_frames(self, frame_ids):
        """
        Iterate over frames specified by their IDs.

        Parameters
        ----------
        frame_ids : iterable of int
            The IDs of the frames to iterate over.

        Yields
        ------
        np.ndarray
            The frames as NumPy arrays.
        """
        for i in frame_ids:
            yield self.get_frame(i)

    def iter_slice(self, slice_: slice):
        """
        Iterate over frames specified by a slice.

        Parameters
        ----------
        slice_ : slice
            The slice object specifying the range of frames.

        Returns
        -------
        generator
            A generator yielding frames as NumPy arrays.
        """
        return self.iter_frames(range(*slice_.indices(self.n_frames)))

    def iter_continuous_slice(self, start: int, stop: int):
        """
        Iterate over a continuous range of frames.

        Parameters
        ----------
        start : int
            The starting frame ID (inclusive).
        stop : int
            The stopping frame ID (exclusive).

        Returns
        -------
        generator
            A generator yielding frames as NumPy arrays.
        """
        return self.iter_slice(slice(start, stop))

    def iter_all_frames(self):
        """
        Iterate over all frames in the video.

        Returns
        -------
        generator
            A generator yielding all frames as NumPy arrays.
        """
        return self.iter_continuous_slice(0, self.n_frames)

    @property
    @abstractmethod
    def n_frames(self) -> int:
        """
        Number of frames in the video.

        Returns
        -------
        int
            The total number of frames.
        """
        pass

    @property
    @abstractmethod
    def fps(self) -> float:
        """
        Frames per second of the video.

        Returns
        -------
        float
            The frame rate of the video.
        """
        pass

    @property
    @abstractmethod
    def width(self) -> int:
        """
        Width of each frame.

        Returns
        -------
        int
            The width of the frames in pixels.
        """
        pass

    @property
    @abstractmethod
    def height(self) -> int:
        """
        Height of each frame.

        Returns
        -------
        int
            The height of the frames in pixels.
        """
        pass

    @property
    def shape(self) -> tuple[int, int, int] | tuple[int, int, int, int]:
        """
        Shape of each frame.

        Returns
        -------
        tuple
            The shape of the frames. If `to_gray` is True, the shape is
            (n_frames, height, width). Otherwise, it is
            (n_frames, height, width, 3).
        """
        if self._to_gray:
            return self.n_frames, self.height, self.width
        else:
            return self.n_frames, self.height, self.width, 3

    def close(self):
        """
        Close the video file.

        This method can be overridden by subclasses to release resources.
        """
        pass

    @property
    def dtype(self) -> np.dtype:
        """
        Data type of the frames.

        Returns
        -------
        np.dtype
            The data type of the frames. Assumed to be `np.uint8`.
        """
        return np.uint8

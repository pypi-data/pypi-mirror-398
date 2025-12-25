from functools import cache, cached_property
import numpy as np
from os import PathLike
from ._reader_backends import ReaderBackend

__all__ = ["VideoReader"]


class VideoReader:
    """
    A class for reading video files with slicing support.

    Parameters
    ----------
    path : str or PathLike
        Path to the video file.
    to_gray : bool, optional
        Whether to convert frames to grayscale. Default is False.
    backend : str, optional
        The backend to use for reading the video. Default is "cv2".

    Attributes
    ----------
    fps : float
        Frames per second of the video.
    width : int
        Width of each frame in pixels.
    height : int
        Height of each frame in pixels.
    shape : tuple
        Shape of the video frames. If `to_gray` is True, the shape is
        (n_frames, height, width). Otherwise, it is
        (n_frames, height, width, 3).
    dtype : np.dtype
        Data type of the video frames.
    """

    def __init__(self, path: str | PathLike, to_gray=False, backend="cv2"):
        self._backend = ReaderBackend.from_name(backend)(path, to_gray=to_gray)

    def _get_frames_iter(self, key):
        """
        Get an iterator for frames based on the key.

        Parameters
        ----------
        key : slice, int, list, np.ndarray, or Ellipsis
            The key specifying which frames to retrieve.

        Returns
        -------
        iterator
            An iterator over the requested frames.
        """
        if key is Ellipsis:
            key = slice(None)
        if isinstance(key, slice):
            if key.step is None or key.step == 1:
                start, stop = key.indices(self._backend.n_frames)[:2]
                return self._backend.iter_continuous_slice(start, stop)
            return self._backend.iter_slice(key)
        key = np.asarray(key)
        if key.ndim == 1:
            return self._backend.iter_frames(key)
        if key.ndim > 1:
            return (np.asarray(tuple(self._get_frames_iter(key_))) for key_ in key)
        return self._backend.get_frame(key)

    def __getitem__(self, key) -> np.ndarray:
        """
        Retrieve/slice frames based on the given key.

        Parameters
        ----------
        key : int, slice, tuple, list, np.ndarray, or Ellipsis
            The key specifying which frames to retrieve.

        Returns
        -------
        np.ndarray
            The requested frames as a NumPy array.
        """
        if np.issubdtype(type(key), np.integer):
            return self._backend.get_frame(key)

        if key is None:
            return self[:][None]

        if isinstance(key, tuple):
            if len(key) == 0:
                # a[()] is equivalent to a[:]
                return self[:]

            key0 = key[0]
            key1 = key[1:]

            if np.issubdtype(type(key0), np.integer):
                return self._backend.get_frame(key0)[key1]

            if key0 is None:
                return self[key1][None]

            if key0 is Ellipsis:
                if Ellipsis in key1:
                    raise IndexError("an index can only have a single ellipsis ('...')")
                key1 = (..., *key1)  # need to propagate ellipsis

            frames = np.asarray([im[key1] for im in self._get_frames_iter(key0)])
            if frames.shape == (0,):
                # handle empty cases like a[:0, ...]
                key1 = (slice(None), *key1)
                frames = np.empty((0, *self.shape[1:]), dtype=self.dtype)[key1]
            return frames

        # handle slice, list, np.ndarray, etc.
        frames = np.asarray([im for im in self._get_frames_iter(key)])
        if frames.shape == (0,):
            # handle empty cases like a[:0] and a[[]]
            frames = np.empty((0, *self.shape[1:]), dtype=self.dtype)
        return frames

    def __iter__(self):
        """
        Iterate over all frames in the video.

        Yields
        ------
        np.ndarray
            Frames as NumPy arrays.
        """
        return self._backend.iter_all_frames()

    def __array__(self, dtype=None, copy=None):
        """
        Convert the video to a NumPy array.

        Parameters
        ----------
        dtype : data-type, optional
            Desired data type of the array. Default is the video's dtype.
        copy : bool, optional
            Whether to copy the data. Default is None.

        Returns
        -------
        np.ndarray
            The video as a NumPy array.
        """
        if dtype is None:
            dtype = self.dtype
        return self[:].astype(dtype)

    @cache
    def __len__(self):
        """
        Get the total number of frames in the video.

        Returns
        -------
        int
            The total number of frames.
        """
        return self._backend.n_frames

    @cached_property
    def fps(self) -> float:
        """
        Frames per second of the video.

        Returns
        -------
        float
            The frame rate of the video.
        """
        return self._backend.fps

    @cached_property
    def width(self) -> int:
        """
        Width of each frame in pixels.

        Returns
        -------
        int
            The width of the frames.
        """
        return self._backend.width

    @cached_property
    def height(self) -> int:
        """
        Height of each frame in pixels.

        Returns
        -------
        int
            The height of the frames.
        """
        return self._backend.height

    @cached_property
    def shape(self) -> tuple[int, int, int, int] | tuple[int, int, int]:
        """
        Shape of the video frames.

        Returns
        -------
        tuple
            The shape of the frames. If `to_gray` is True, the shape is
            (n_frames, height, width). Otherwise, it is
            (n_frames, height, width, 3).
        """
        return self._backend.shape

    @cached_property
    def dtype(self) -> np.dtype:
        """
        Data type of the video frames.

        Returns
        -------
        np.dtype
            The data type of the frames.
        """
        return self._backend.dtype

    def close(self):
        """
        Close the video reader and release any resources.
        """
        self._backend.close()
        self._backend = None

    def __enter__(self):
        """
        Enter the runtime context for the video reader.

        Returns
        -------
        VideoReader
            The video reader instance.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the runtime context for the video reader.

        Parameters
        ----------
        exc_type : type
            The exception type.
        exc_val : Exception
            The exception value.
        exc_tb : traceback
            The traceback object.

        Returns
        -------
        bool
            False to propagate the exception, if any.
        """
        self.close()
        return False

    def __del__(self):
        """
        Destructor to ensure the video reader is properly closed.
        """
        self.close()

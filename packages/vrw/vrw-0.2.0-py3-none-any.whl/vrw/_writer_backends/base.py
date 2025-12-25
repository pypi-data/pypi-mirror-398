from abc import ABC, abstractmethod
import numpy as np


class WriterBackend(ABC):
    """
    Abstract base class for video writer backends.

    Parameters
    ----------
    filename : str
        The name of the file where the video will be written.
    fps : float
        The frame rate of the video in frames per second.
    """

    def __init__(self, filename: str, fps: float):
        self._filename = filename
        self._fps = fps
        self._n_frames = 0

    @staticmethod
    def from_name(name: str):
        """
        Create a WriterBackend instance from a name.

        Parameters
        ----------
        name : str
            Name of the backend.

        Returns
        -------
        WriterBackend
            The backend class corresponding to the given name.

        Raises
        ------
        ValueError
            If the backend name is not recognized.
        """
        if name == "cv2":
            from .cv2_backend import Cv2Backend

            return Cv2Backend
        elif name == "pyav":
            from .pyav_backend import PyAvBackend

            return PyAvBackend
        raise ValueError(f"Unknown backend: {name}. Available backends: cv2, pyav")

    @abstractmethod
    def write(self, frame: np.ndarray):
        """
        Write a single frame to the video file.

        Parameters
        ----------
        frame : np.ndarray
            The frame to write, represented as a NumPy array.
        """
        pass

    @abstractmethod
    def _init(self, frame_shape: tuple):
        """
        Initialize the video writer with the shape of the frames.

        Parameters
        ----------
        frame_shape : tuple
            The shape of the frames to be written.
        """
        pass

    def close(self):
        """
        Close the video writer and release any resources.

        This method can be overridden by subclasses to perform cleanup.
        """
        pass

    def __len__(self):
        """
        Get the number of frames written to the video.

        Returns
        -------
        int
            The total number of frames written.
        """
        return self._n_frames

    def __del__(self):
        """
        Destructor to ensure the video writer is properly closed.
        """
        self.close()

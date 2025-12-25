from ._writer_backends import WriterBackend
import numpy as np

__all__ = ["VideoWriter"]


class VideoWriter:
    """
    A class for writing video files using different backends.

    Parameters
    ----------
    filename : str
        The name of the file where the video will be written.
    fps : float
        The frame rate of the video in frames per second.
    backend : str, optional
        The backend to use for writing the video. Default is "cv2".
    **kwargs : dict, optional
        Additional arguments to pass to the backend.

    Methods
    -------
    write(frame)
        Write a single frame to the video file.
    close()
        Close the video writer and release resources.
    """

    def __init__(self, filename: str, fps: float, backend: str = "cv2", **kwargs):
        """
        Initialize the VideoWriter.

        Parameters
        ----------
        filename : str
            The name of the file where the video will be written.
        fps : float
            The frame rate of the video in frames per second.
        backend : str, optional
            The backend to use for writing the video. Default is "cv2".
        **kwargs : dict, optional
            Additional arguments to pass to the backend.
        """
        self._backend = WriterBackend.from_name(backend)(filename, fps, **kwargs)

    def write(self, frame: np.ndarray):
        """
        Write a single frame to the video file.

        Parameters
        ----------
        frame : np.ndarray
            The frame to write, represented as a NumPy array.
        """
        self._backend.write(frame)

    def close(self):
        """
        Close the video writer and release any resources.
        """
        self._backend.close()

    def __enter__(self):
        """
        Enter the runtime context for the video writer.

        Returns
        -------
        VideoWriter
            The video writer instance.
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Exit the runtime context for the video writer.

        Parameters
        ----------
        exc_type : type
            The exception type.
        exc_value : Exception
            The exception value.
        traceback : traceback
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
        Destructor to ensure the video writer is properly closed.
        """
        self.close()

    def __len__(self):
        """
        Get the number of frames written to the video.

        Returns
        -------
        int
            The total number of frames written.
        """
        return len(self._backend)

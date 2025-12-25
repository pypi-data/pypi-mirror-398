import numpy as np
import pytest

from vrw import VideoReader, VideoWriter

try:
    HAS_CV2 = True
except Exception:
    HAS_CV2 = False

try:
    HAS_AV = True
except Exception:
    HAS_AV = False

try:
    from video_reader import PyVideoReader  # noqa: F401

    HAS_RUST = True
except Exception:
    HAS_RUST = False


CV2_ONLY = pytest.mark.skipif(not HAS_CV2, reason="cv2 backend not available")
PYAV_ONLY = pytest.mark.skipif(not HAS_AV, reason="pyav backend not available")
RUST_ONLY = pytest.mark.skipif(not HAS_RUST, reason="rust backend not available")


@pytest.fixture
def color_frames():
    values = [0, 64, 128, 192, 255]
    return [np.full((4, 6, 3), v, dtype=np.uint8) for v in values]


@pytest.fixture
def write_video(tmp_path, color_frames):
    def _write(backend: str, filename: str, **kwargs):
        path = tmp_path / filename
        with VideoWriter(str(path), fps=24, backend=backend, **kwargs) as writer:
            for frame in color_frames:
                writer.write(frame)
        return path, color_frames

    return _write


@pytest.fixture
@CV2_ONLY
def sample_video_cv2(write_video):
    return write_video("cv2", "sample_cv2.avi", fourcc="MJPG")


@pytest.fixture
@PYAV_ONLY
def sample_video_pyav(write_video):
    return write_video("pyav", "sample_pyav.mp4")


@pytest.mark.parametrize(
    "backend,kwargs",
    [
        pytest.param("cv2", {"fourcc": "MJPG"}, marks=CV2_ONLY),
        pytest.param("pyav", {}, marks=PYAV_ONLY),
    ],
)
def test_video_writer_counts(tmp_path, color_frames, backend, kwargs):
    ext = "avi" if backend == "cv2" else "mp4"
    path = tmp_path / f"writer_{backend}.{ext}"
    writer = VideoWriter(str(path), fps=24, backend=backend, **kwargs)
    with writer:
        for frame in color_frames:
            writer.write(frame)
    assert len(writer) == len(color_frames)
    assert path.exists()
    assert path.stat().st_size > 0


@pytest.mark.parametrize(
    "reader_backend",
    [
        pytest.param("cv2", marks=CV2_ONLY),
        pytest.param("rust", marks=RUST_ONLY),
    ],
)
def test_video_reader_basic_indexing(sample_video_cv2, reader_backend):
    path, frames = sample_video_cv2
    with VideoReader(str(path), backend=reader_backend) as reader:
        assert len(reader) == len(frames)
        assert reader.shape == (
            len(frames),
            frames[0].shape[0],
            frames[0].shape[1],
            3,
        )
        np.testing.assert_allclose(reader[0], frames[0], atol=2)
        np.testing.assert_allclose(reader[-1], frames[-1], atol=2)
        np.testing.assert_allclose(reader[1:3], frames[1:3], atol=2)
        np.testing.assert_allclose(
            reader[[0, 2, 4]], [frames[0], frames[2], frames[4]], atol=2
        )
        channel0 = reader[..., 0]
        expected_channel0 = np.stack([frame[..., 0] for frame in frames])
        np.testing.assert_allclose(channel0, expected_channel0, atol=2)
        assert reader[:0].shape == (0, frames[0].shape[0], frames[0].shape[1], 3)
        assert reader[[]].shape == (0, frames[0].shape[0], frames[0].shape[1], 3)


@pytest.mark.parametrize(
    "reader_backend",
    [
        pytest.param("cv2", marks=CV2_ONLY),
        pytest.param("rust", marks=RUST_ONLY),
    ],
)
def test_video_reader_to_gray(sample_video_cv2, reader_backend):
    path, frames = sample_video_cv2
    with VideoReader(str(path), backend=reader_backend, to_gray=True) as reader:
        gray = reader[:]
        assert gray.shape == (
            len(frames),
            frames[0].shape[0],
            frames[0].shape[1],
        )
        expected_gray = np.stack([frame[..., 0] for frame in frames])
        np.testing.assert_allclose(gray, expected_gray, atol=2)


@pytest.mark.parametrize(
    "reader_backend",
    [
        pytest.param("cv2", marks=CV2_ONLY),
        pytest.param("rust", marks=RUST_ONLY),
    ],
)
def test_video_reader_iter(sample_video_cv2, reader_backend):
    path, frames = sample_video_cv2
    with VideoReader(str(path), backend=reader_backend) as reader:
        iterated = list(reader)
    np.testing.assert_allclose(iterated, frames, atol=2)


@pytest.mark.parametrize(
    "reader_backend",
    [
        pytest.param("cv2", marks=CV2_ONLY),
        pytest.param("rust", marks=RUST_ONLY),
    ],
)
def test_video_reader_array_interface(sample_video_cv2, reader_backend):
    path, frames = sample_video_cv2
    with VideoReader(str(path), backend=reader_backend) as reader:
        arr = np.array(reader)
    np.testing.assert_allclose(arr, frames, atol=2)


@PYAV_ONLY
@CV2_ONLY
def test_pyav_writer_cv2_reader(sample_video_pyav):
    path, frames = sample_video_pyav
    with VideoReader(str(path), backend="cv2") as reader:
        arr = np.array(reader)
    np.testing.assert_allclose(arr, frames, atol=2)

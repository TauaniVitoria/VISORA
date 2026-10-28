"""
Testes unitários para o módulo VideoReader.
Valida verificação de existência, integridade, extração de metadados,
iteração de quadros, cálculo de timestamps e liberação de recursos.
"""

from pathlib import Path
import cv2
import numpy as np
import pytest

from alpr.video_reader import (
    VideoCorruptedError,
    VideoFileNotFoundError,
    VideoReader,
)


@pytest.fixture
def synthetic_video_file(tmp_path: Path) -> Path:
    """Cria um arquivo de vídeo sintético de 10 quadros para testes."""
    video_path = tmp_path / "test_synth.mp4"
    width, height, fps = 320, 240, 20.0
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(video_path), fourcc, fps, (width, height))

    for i in range(10):
        # Gera quadro sintético com gradiente e contador
        frame = np.full((height, width, 3), fill_value=i * 20, dtype=np.uint8)
        cv2.putText(frame, f"Frame {i}", (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        writer.write(frame)

    writer.release()
    return video_path


def test_video_reader_file_not_found():
    """Valida que arquivo inexistente levanta VideoFileNotFoundError."""
    with pytest.raises(VideoFileNotFoundError):
        VideoReader("caminho/completamente/inexistente/video.mp4")


def test_video_reader_empty_file(tmp_path: Path):
    """Valida que arquivo vazio de 0 bytes levanta VideoCorruptedError."""
    empty_file = tmp_path / "empty.mp4"
    empty_file.touch()
    with pytest.raises(VideoCorruptedError):
        VideoReader(empty_file)


def test_video_reader_metadata(synthetic_video_file: Path):
    """Valida a extração de resolução, FPS e duração."""
    with VideoReader(synthetic_video_file) as reader:
        meta = reader.metadata
        assert meta.width == 320
        assert meta.height == 240
        assert meta.fps == 20.0
        assert meta.total_frames == 10
        assert abs(meta.duration_seconds - 0.5) < 0.05


def test_video_reader_sequential_iteration(synthetic_video_file: Path):
    """Valida a extração sequencial e precisão dos timestamps."""
    with VideoReader(synthetic_video_file) as reader:
        frames = list(reader.read_frames())
        assert len(frames) == 10

        for idx, f in enumerate(frames):
            assert f.frame_idx == idx
            assert f.image.shape == (240, 320, 3)
            # Timestamp esperado: frame_idx / fps (com tolerância)
            expected_sec = idx / 20.0
            assert abs(f.timestamp_seconds - expected_sec) < 0.1


def test_video_reader_max_frames(synthetic_video_file: Path):
    """Valida o limitador de max_frames."""
    with VideoReader(synthetic_video_file) as reader:
        frames = list(reader.read_frames(max_frames=4))
        assert len(frames) == 4
        assert frames[-1].frame_idx == 3


def test_video_reader_release(synthetic_video_file: Path):
    """Valida que o context manager fecha a captura corretamente."""
    reader = VideoReader(synthetic_video_file)
    assert reader._cap is not None and reader._cap.isOpened()
    reader.release()
    assert reader._cap is None


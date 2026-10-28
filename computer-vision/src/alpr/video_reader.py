"""
Módulo de leitura e decodificação de vídeos locais com OpenCV.
Valida arquivos, extrai metadados e itera sobre quadros com registro de timestamps.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Generator, Optional, Tuple
import cv2
import numpy as np


class VideoReaderError(Exception):
    """Exceção base para erros relacionados ao VideoReader."""
    pass


class VideoFileNotFoundError(VideoReaderError):
    """Lançada quando o arquivo de vídeo não existe."""
    pass


class VideoCorruptedError(VideoReaderError):
    """Lançada quando o vídeo não pôde ser aberto ou está corrompido."""
    pass


@dataclass(frozen=True)
class VideoMetadata:
    """Metadados estruturados do arquivo de vídeo."""
    file_path: str
    width: int
    height: int
    fps: float
    total_frames: int
    duration_seconds: float


@dataclass
class VideoFrame:
    """Estrutura que encapsula um quadro e seus metadados de captura."""
    frame_idx: int
    timestamp_ms: float
    timestamp_seconds: float
    image: np.ndarray


class VideoReader:
    """
    Leitor sequencial de vídeos locais baseado em OpenCV VideoCapture.
    
    Suporta gerenciamento de contexto (with), validação estrita de integridade
    e cálculo de timestamps por frame.
    """

    def __init__(self, video_path: str | Path):
        self.video_path = Path(video_path).resolve()
        self._cap: Optional[cv2.VideoCapture] = None
        self._metadata: Optional[VideoMetadata] = None
        self._validate_and_open()

    def _validate_and_open(self) -> None:
        """Valida a existência do arquivo e inicializa o VideoCapture."""
        if not self.video_path.exists():
            raise VideoFileNotFoundError(f"Arquivo de vídeo não encontrado: {self.video_path}")
        
        if not self.video_path.is_file() or self.video_path.stat().st_size == 0:
            raise VideoCorruptedError(f"Arquivo de vídeo inválido ou vazio: {self.video_path}")

        self._cap = cv2.VideoCapture(str(self.video_path))
        if not self._cap.isOpened():
            raise VideoCorruptedError(f"Não foi possível abrir o arquivo de vídeo: {self.video_path}")

        width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = float(self._cap.get(cv2.CAP_PROP_FPS))
        total_frames = int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Tratar FPS inválido ou zerado (comum em arquivos corrompidos ou webm mal codificados)
        if fps <= 0:
            fps = 30.0  # Fallback padrão seguro

        duration = (total_frames / fps) if total_frames > 0 else 0.0

        self._metadata = VideoMetadata(
            file_path=str(self.video_path),
            width=width,
            height=height,
            fps=fps,
            total_frames=total_frames,
            duration_seconds=duration,
        )

    @property
    def metadata(self) -> VideoMetadata:
        """Retorna os metadados do vídeo aberto."""
        if self._metadata is None:
            raise VideoReaderError("Vídeo ainda não foi inicializado.")
        return self._metadata

    def read_frames(self, start_frame: int = 0, max_frames: Optional[int] = None) -> Generator[VideoFrame, None, None]:
        """
        Gera quadros sequenciais com metadados temporais.
        
        Args:
            start_frame: Índice inicial do quadro (0-indexado).
            max_frames: Quantidade máxima de quadros para ler (None para ler até o fim).
        
        Yields:
            VideoFrame contendo o índice, timestamp e a imagem BGR.
        """
        if self._cap is None or not self._cap.isOpened():
            raise VideoReaderError("Captura de vídeo fechada ou não inicializada.")

        if start_frame > 0:
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        frame_idx = start_frame
        frames_yielded = 0

        while self._cap.isOpened():
            if max_frames is not None and frames_yielded >= max_frames:
                break

            ret, frame = self._cap.read()
            if not ret or frame is None:
                break

            # Obter timestamp do OpenCV ou calcular com base no FPS
            pos_msec = self._cap.get(cv2.CAP_PROP_POS_MSEC)
            if pos_msec <= 0:
                pos_msec = (frame_idx / self.metadata.fps) * 1000.0

            timestamp_sec = pos_msec / 1000.0

            yield VideoFrame(
                frame_idx=frame_idx,
                timestamp_ms=pos_msec,
                timestamp_seconds=timestamp_sec,
                image=frame,
            )

            frame_idx += 1
            frames_yielded += 1

    def release(self) -> None:
        """Libera os recursos do VideoCapture."""
        if self._cap is not None:
            if self._cap.isOpened():
                self._cap.release()
            self._cap = None

    def __enter__(self) -> "VideoReader":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.release()

    def __del__(self) -> None:
        self.release()

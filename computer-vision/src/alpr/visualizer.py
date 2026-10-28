"""
Módulo de renderização visual e gravação de vídeo anotado.
Desenha caixas delimitadoras de veículos e placas, rótulos de identificação,
confiança de OCR e painel de telemetria sobre os quadros.
"""

from pathlib import Path
from typing import List, Optional, Tuple
import cv2
import numpy as np


class Visualizer:
    """
    Renderizador visual para anotações em tempo real e exportação de vídeo anotado.
    """

    def __init__(
        self,
        vehicle_box_color: Tuple[int, int, int] = (0, 165, 255),  # BGR Laranja
        plate_box_color: Tuple[int, int, int] = (0, 255, 0),       # BGR Verde
        text_color: Tuple[int, int, int] = (255, 255, 255),        # BGR Branco
        text_bg_color: Tuple[int, int, int] = (0, 0, 0),           # BGR Preto
        font_scale: float = 0.6,
        bbox_thickness: int = 2,
    ):
        self.vehicle_box_color = vehicle_box_color
        self.plate_box_color = plate_box_color
        self.text_color = text_color
        self.text_bg_color = text_bg_color
        self.font_scale = font_scale
        self.bbox_thickness = bbox_thickness
        self.font = cv2.FONT_HERSHEY_SIMPLEX

    def draw_bbox_with_label(
        self,
        image: np.ndarray,
        bbox: Tuple[int, int, int, int],
        label: str,
        color: Tuple[int, int, int],
        confidence: Optional[float] = None,
    ) -> np.ndarray:
        """
        Desenha uma bounding box retangular com fundo contrastante para o texto.

        Args:
            image: Imagem de entrada BGR (será modificada in-place).
            bbox: (x1, y1, x2, y2).
            label: Texto do rótulo principal.
            color: Cor da borda BGR.
            confidence: Confiança opcional [0.0, 1.0].
        """
        x1, y1, x2, y2 = bbox
        cv2.rectangle(image, (x1, y1), (x2, y2), color, self.bbox_thickness)

        full_label = f"{label} {confidence:.2f}" if confidence is not None else label

        # Calcular dimensões do texto para o fundo sólido
        (text_w, text_h), baseline = cv2.getTextSize(full_label, self.font, self.font_scale, 1)
        bg_y1 = max(0, y1 - text_h - 8)
        bg_y2 = y1
        bg_x2 = min(image.shape[1], x1 + text_w + 8)

        # Fundo do texto para máxima legibilidade
        cv2.rectangle(image, (x1, bg_y1), (bg_x2, bg_y2), self.text_bg_color, -1)
        cv2.putText(
            image,
            full_label,
            (x1 + 4, y1 - 4),
            self.font,
            self.font_scale,
            color,
            1,
            cv2.LINE_AA,
        )
        return image

    def draw_telemetry(
        self,
        image: np.ndarray,
        frame_idx: int,
        fps: float,
        active_tracks: int,
        confirmed_plates: int,
    ) -> np.ndarray:
        """Desenha a barra superior de telemetria e métricas de desempenho."""
        h, w = image.shape[:2]
        bar_height = 36

        # Barra translúcida no topo
        overlay = image.copy()
        cv2.rectangle(overlay, (0, 0), (w, bar_height), (20, 20, 20), -1)
        cv2.addWeighted(overlay, 0.75, image, 0.25, 0, image)

        status_text = f"Frame: {frame_idx:05d} | FPS: {fps:.1f} | Veiculos Ativos: {active_tracks} | Placas Confirmadas: {confirmed_plates}"
        cv2.putText(image, status_text, (15, 24), self.font, 0.55, (240, 240, 240), 1, cv2.LINE_AA)
        return image


class VideoWriterOutput:
    """Gerenciador do OpenCV VideoWriter para gravação do resultado anotado."""

    def __init__(self, output_path: str | Path, fps: float, frame_size: Tuple[int, int]):
        self.output_path = Path(output_path).resolve()
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.fps = fps
        self.frame_size = frame_size  # (width, height)
        self._writer: Optional[cv2.VideoWriter] = None
        self._init_writer()

    def _init_writer(self) -> None:
        """Inicializa o codec e o writer."""
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self._writer = cv2.VideoWriter(
            str(self.output_path),
            fourcc,
            self.fps,
            self.frame_size,
        )

    def write_frame(self, frame: np.ndarray) -> None:
        """Grava um quadro processado."""
        if self._writer is not None and self._writer.isOpened():
            self._writer.write(frame)

    def release(self) -> None:
        """Finaliza a escrita do arquivo de vídeo."""
        if self._writer is not None:
            if self._writer.isOpened():
                self._writer.release()
            self._writer = None

    def __enter__(self) -> "VideoWriterOutput":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.release()

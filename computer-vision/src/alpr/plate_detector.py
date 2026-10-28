"""
Módulo de detecção especializada de placas veiculares utilizando YOLO.
Detecta placas em regiões de veículos ou quadros completos e mapeia coordenadas
para o sistema de referência da imagem original.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple
import cv2
import numpy as np
from ultralytics import YOLO


@dataclass
class PlateDetection:
    """Estrutura com os dados de localização e recorte da placa."""
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2) no sistema de coordenadas da imagem original
    local_bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2) relativo à ROI do veículo
    confidence: float
    crop: np.ndarray  # Imagem recortada da placa (BGR)
    aspect_ratio: float  # largura / altura


class PlateDetector:
    """
    Detector especializado de placas veiculares.
    
    Projetado para operar sobre os recortes dos veículos (VehicleDetection.crop),
    convertendo com precisão as coordenadas relativas para o quadro original.
    """

    def __init__(
        self,
        model_path: str = "models/weights/plate_detector_yolo.pt",
        confidence_threshold: float = 0.4,
        iou_threshold: float = 0.4,
        min_aspect_ratio: float = 1.5,
        max_aspect_ratio: float = 4.5,
        device: str = "auto",
    ):
        self.model_path = Path(model_path)
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.min_aspect_ratio = min_aspect_ratio
        self.max_aspect_ratio = max_aspect_ratio
        self.device = self._resolve_device(device)
        self.model: Optional[YOLO] = None
        self._load_model_if_available()

    def _resolve_device(self, requested_device: str) -> str:
        """Resolve o dispositivo de aceleração (mps, cpu, cuda ou auto)."""
        import torch

        if requested_device == "auto":
            if torch.backends.mps.is_available():
                return "mps"
            elif torch.cuda.is_available():
                return "cuda"
            return "cpu"
        return requested_device

    def _load_model_if_available(self) -> None:
        """
        Carrega os pesos dedicados de detecção de placas caso o arquivo exista.
        Não gera pesos fictícios caso o arquivo não seja encontrado.
        """
        if self.model_path.exists() and self.model_path.is_file():
            self.model = YOLO(str(self.model_path))
        else:
            self.model = None

    @property
    def is_model_available(self) -> bool:
        """Indica se os pesos do modelo especializado de placas estão carregados."""
        return self.model is not None

    def detect_in_vehicle(
        self,
        vehicle_crop: np.ndarray,
        vehicle_bbox: Tuple[int, int, int, int],
        frame_shape: Tuple[int, int],
    ) -> List[PlateDetection]:
        """
        Detecta placas dentro da ROI recortada de um veículo e projeta
        as coordenadas de volta para o referencial da imagem original.

        Args:
            vehicle_crop: Imagem da região do veículo (BGR).
            vehicle_bbox: (vx1, vy1, vx2, vy2) do veículo na imagem original.
            frame_shape: (height, width) da imagem original para validação de limites.

        Returns:
            Lista de PlateDetection encontradas na ROI do veículo.
        """
        if not self.is_model_available:
            return []

        if vehicle_crop is None or vehicle_crop.size == 0:
            return []

        h_veh, w_veh = vehicle_crop.shape[:2]
        h_orig, w_orig = frame_shape[:2]
        vx1, vy1, _, _ = vehicle_bbox

        results = self.model.predict(
            source=vehicle_crop,
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            device=self.device,
            verbose=False,
        )

        detections: List[PlateDetection] = []

        if not results or len(results) == 0:
            return detections

        boxes = results[0].boxes
        if boxes is None or len(boxes) == 0:
            return detections

        for box in boxes:
            conf = float(box.conf[0].item())
            xyxy = box.xyxy[0].cpu().numpy()

            # Coordenadas relativas ao recorte do veículo
            lx1 = int(round(xyxy[0]))
            ly1 = int(round(xyxy[1]))
            lx2 = int(round(xyxy[2]))
            ly2 = int(round(xyxy[3]))

            # Clamping aos limites do recorte do veículo
            lx1_c = max(0, min(w_veh - 1, lx1))
            ly1_c = max(0, min(h_veh - 1, ly1))
            lx2_c = max(lx1_c + 1, min(w_veh, lx2))
            ly2_c = max(ly1_c + 1, min(h_veh, ly2))

            crop_w = lx2_c - lx1_c
            crop_h = ly2_c - ly1_c

            if crop_h <= 0 or crop_w <= 0:
                continue

            aspect_ratio = float(crop_w) / float(crop_h)

            # Filtro de proporção (aspect ratio) para placas veiculares
            if not (self.min_aspect_ratio <= aspect_ratio <= self.max_aspect_ratio):
                continue

            # Conversão para as coordenadas da imagem original
            gx1 = max(0, min(w_orig - 1, vx1 + lx1_c))
            gy1 = max(0, min(h_orig - 1, vy1 + ly1_c))
            gx2 = max(gx1 + 1, min(w_orig, vx1 + lx2_c))
            gy2 = max(gy1 + 1, min(h_orig, vy1 + ly2_c))

            plate_crop = vehicle_crop[ly1_c:ly2_c, lx1_c:lx2_c].copy()

            if plate_crop.size == 0:
                continue

            detections.append(
                PlateDetection(
                    bbox=(gx1, gy1, gx2, gy2),
                    local_bbox=(lx1_c, ly1_c, lx2_c, ly2_c),
                    confidence=conf,
                    crop=plate_crop,
                    aspect_ratio=aspect_ratio,
                )
            )

        return detections

    def detect_in_frame(self, frame: np.ndarray) -> List[PlateDetection]:
        """
        Executa a detecção de placas diretamente sobre o quadro completo.
        Útil para validações de teste ou fallbacks onde o recorte de veículo não é utilizado.
        """
        if not self.is_model_available or frame is None or frame.size == 0:
            return []

        h_orig, w_orig = frame.shape[:2]
        return self.detect_in_vehicle(
            vehicle_crop=frame,
            vehicle_bbox=(0, 0, w_orig, h_orig),
            frame_shape=(h_orig, w_orig),
        )


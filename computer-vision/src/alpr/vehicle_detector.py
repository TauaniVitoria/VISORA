"""
Módulo de detecção de veículos utilizando modelos YOLO (Ultralytics).
Detecta carros, ônibus, caminhões e motocicletas, extraindo bounding boxes e ROIs.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union
import cv2
import numpy as np
from ultralytics import YOLO


@dataclass
class VehicleDetection:
    """Detecção estruturada de um veículo em um quadro."""
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2) coordenadas absolutas no quadro
    confidence: float
    class_id: int
    class_name: str
    crop: np.ndarray  # Imagem recortada da região do veículo


class VehicleDetector:
    """
    Detector de veículos baseado em YOLO pré-treinado (COCO).
    Filtra classes de interesse (carros, ônibus, caminhões) e recorta as ROIs.
    """

    # Mapeamento padrão de classes veiculares do dataset COCO
    COCO_VEHICLE_CLASSES: Dict[int, str] = {
        2: "car",
        3: "motorcycle",
        5: "bus",
        7: "truck",
    }

    def __init__(
        self,
        model_name: str = "yolov8n.pt",
        confidence_threshold: float = 0.5,
        iou_threshold: float = 0.45,
        target_classes: Optional[List[int]] = None,
        crop_padding_px: int = 10,
        device: str = "auto",
    ):
        self.model_name = model_name
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.target_classes = target_classes or [2, 3, 5, 7]
        self.crop_padding_px = crop_padding_px
        self.device = self._resolve_device(device)
        self.model = self._load_model()

    def _resolve_device(self, requested_device: str) -> str:
        """Resolve o dispositivo de execução (mps, cpu, cuda ou auto)."""
        import torch

        if requested_device == "auto":
            if torch.backends.mps.is_available():
                return "mps"
            elif torch.cuda.is_available():
                return "cuda"
            return "cpu"
        return requested_device

    def _load_model(self) -> YOLO:
        """Carrega o modelo YOLO utilizando a biblioteca ultralytics."""
        model = YOLO(self.model_name)
        return model

    def detect(self, frame: np.ndarray) -> List[VehicleDetection]:
        """
        Executa a detecção de veículos no quadro fornecido.

        Args:
            frame: Imagem BGR (numpy array).

        Returns:
            Lista de VehicleDetection com coordenadas e recortes dos veículos.
        """
        if frame is None or frame.size == 0:
            return []

        h_img, w_img = frame.shape[:2]

        results = self.model.predict(
            source=frame,
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            classes=self.target_classes,
            device=self.device,
            verbose=False,
        )

        detections: List[VehicleDetection] = []

        if not results or len(results) == 0:
            return detections

        first_res = results[0]
        boxes = first_res.boxes

        if boxes is None or len(boxes) == 0:
            return detections

        for box in boxes:
            cls_id = int(box.cls[0].item())
            conf = float(box.conf[0].item())
            xyxy = box.xyxy[0].cpu().numpy()

            x1 = int(round(xyxy[0]))
            y1 = int(round(xyxy[1]))
            x2 = int(round(xyxy[2]))
            y2 = int(round(xyxy[3]))

            # Clamping das coordenadas aos limites da imagem
            x1_clamped = max(0, min(w_img - 1, x1))
            y1_clamped = max(0, min(h_img - 1, y1))
            x2_clamped = max(x1_clamped + 1, min(w_img, x2))
            y2_clamped = max(y1_clamped + 1, min(h_img, y2))

            # Recorte com padding opcional
            pad = self.crop_padding_px
            crop_x1 = max(0, x1_clamped - pad)
            crop_y1 = max(0, y1_clamped - pad)
            crop_x2 = min(w_img, x2_clamped + pad)
            crop_y2 = min(h_img, y2_clamped + pad)

            crop = frame[crop_y1:crop_y2, crop_x1:crop_x2].copy()

            class_name = self.COCO_VEHICLE_CLASSES.get(cls_id, f"vehicle_{cls_id}")

            detections.append(
                VehicleDetection(
                    bbox=(x1_clamped, y1_clamped, x2_clamped, y2_clamped),
                    confidence=conf,
                    class_id=cls_id,
                    class_name=class_name,
                    crop=crop,
                )
            )

        return detections

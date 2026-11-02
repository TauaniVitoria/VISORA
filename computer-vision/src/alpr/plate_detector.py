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
        candidate = self.model_path
        if not candidate.exists() and str(self.model_path) == "models/weights/plate_detector_yolo.pt":
            cv_root_candidate = Path(__file__).resolve().parents[2] / self.model_path
            if cv_root_candidate.exists():
                candidate = cv_root_candidate
                self.model_path = candidate

        if candidate.exists() and candidate.is_file():
            self.model = YOLO(str(candidate))
        else:
            self.model = None

    @property
    def is_model_available(self) -> bool:
        """Indica se os pesos do modelo especializado de placas estão carregados."""
        return self.model is not None

    def _detect_morphological_candidates(
        self,
        vehicle_crop: np.ndarray,
        vehicle_bbox: Tuple[int, int, int, int],
        frame_shape: Tuple[int, int],
    ) -> List[PlateDetection]:
        """
        Localizador morfológico complementar baseado em Black-Hat, gradiente vertical Sobel-X
        e geometria retangular de placas brasileiras na região frontal/traseira do veículo.
        """
        h_veh, w_veh = vehicle_crop.shape[:2]
        h_orig, w_orig = frame_shape[:2]
        vx1, vy1, _, _ = vehicle_bbox
        detections: List[PlateDetection] = []

        if h_veh < 36 or w_veh < 60 or int(vehicle_crop.max()) == 0:
            return detections

        # 1. Busca por caracteres escuros sobre fundo claro (Black-Hat + Sobel-X) nos 75% inferiores do veículo
        y_start = int(h_veh * 0.25)
        roi = vehicle_crop[y_start:, :]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY) if len(roi.shape) == 3 else roi

        rect_kern = cv2.getStructuringElement(cv2.MORPH_RECT, (17, 5))
        blackhat = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, rect_kern)
        grad_x = cv2.Sobel(blackhat, ddepth=cv2.CV_32F, dx=1, dy=0, ksize=-1)
        grad_x = np.absolute(grad_x)
        min_v, max_v = float(np.min(grad_x)), float(np.max(grad_x))
        if max_v > min_v:
            grad_x = 255.0 * ((grad_x - min_v) / (max_v - min_v))
        grad_x_u8 = grad_x.astype("uint8")
        grad_x_u8 = cv2.GaussianBlur(grad_x_u8, (5, 5), 0)
        grad_x_u8 = cv2.morphologyEx(grad_x_u8, cv2.MORPH_CLOSE, rect_kern)
        _, thresh = cv2.threshold(grad_x_u8, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        thresh = cv2.erode(thresh, None, iterations=1)
        thresh = cv2.dilate(thresh, None, iterations=2)

        cnts, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        scored_boxes: List[Tuple[float, Tuple[int, int, int, int], float]] = []

        for c in cnts:
            x, y, cw, ch = cv2.boundingRect(c)
            if ch <= 0 or cw <= 0:
                continue
            ar = float(cw) / float(ch)
            if 1.8 <= ar <= 6.0 and cw >= 48 and ch >= 14 and cw <= w_veh * 0.70:
                cx = x + cw / 2.0
                center_dist = abs(cx - (w_veh / 2.0)) / max(1.0, (w_veh / 2.0))
                if center_dist > 0.50:
                    continue
                px = int(cw * 0.10)
                py = int(ch * 0.18)
                lx1_c = max(0, x - px)
                ly1_c = max(0, y + y_start - py)
                lx2_c = min(w_veh, x + cw + px)
                ly2_c = min(h_veh, y + y_start + ch + py)
                final_w = lx2_c - lx1_c
                final_h = ly2_c - ly1_c
                if final_h <= 0 or final_w <= 0:
                    continue
                final_ar = float(final_w) / float(final_h)
                if not (self.min_aspect_ratio <= final_ar <= max(self.max_aspect_ratio, 5.5)):
                    continue
                score = (cw * ch) * (1.0 - 0.45 * center_dist)
                conf = min(0.92, max(0.55, 0.85 * (1.0 - 0.3 * center_dist)))
                scored_boxes.append((score, (lx1_c, ly1_c, lx2_c, ly2_c), conf))

        # 2. Busca complementar por retângulo claro de alto contraste (placas sintéticas / iluminação direta)
        if not scored_boxes:
            full_gray = cv2.cvtColor(vehicle_crop, cv2.COLOR_BGR2GRAY) if len(vehicle_crop.shape) == 3 else vehicle_crop
            _, bright_th = cv2.threshold(full_gray, 200, 255, cv2.THRESH_BINARY)
            b_cnts, _ = cv2.findContours(bright_th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for c in b_cnts:
                x, y, cw, ch = cv2.boundingRect(c)
                if ch <= 0 or cw <= 0:
                    continue
                ar = float(cw) / float(ch)
                if self.min_aspect_ratio <= ar <= self.max_aspect_ratio and cw >= 50 and ch >= 16 and cw <= w_veh * 0.95:
                    scored_boxes.append((float(cw * ch), (x, y, x + cw, y + ch), 0.88))

        scored_boxes.sort(key=lambda item: item[0], reverse=True)
        for _, (lx1_c, ly1_c, lx2_c, ly2_c), conf in scored_boxes[:1]:
            crop_w = lx2_c - lx1_c
            crop_h = ly2_c - ly1_c
            aspect_ratio = float(crop_w) / float(crop_h)
            gx1 = max(0, min(w_orig - 1, vx1 + lx1_c))
            gy1 = max(0, min(h_orig - 1, vy1 + ly1_c))
            gx2 = max(gx1 + 1, min(w_orig, vx1 + lx2_c))
            gy2 = max(gy1 + 1, min(h_orig, vy1 + ly2_c))
            plate_crop = vehicle_crop[ly1_c:ly2_c, lx1_c:lx2_c].copy()
            if plate_crop.size > 0:
                detections.append(
                    PlateDetection(
                        bbox=(gx1, gy1, gx2, gy2),
                        local_bbox=(lx1_c, ly1_c, lx2_c, ly2_c),
                        confidence=round(conf, 4),
                        crop=plate_crop,
                        aspect_ratio=round(aspect_ratio, 4),
                    )
                )
        return detections

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

        # Seleciona a placa de maior confiança para o veículo atual
        if len(detections) > 1:
            detections.sort(key=lambda d: d.confidence, reverse=True)
            detections = detections[:1]

        # Fallback morfológico quando o modelo real YOLO não captura placas pequenas/sombreadas
        if not detections and isinstance(self.model, YOLO):
            detections = self._detect_morphological_candidates(
                vehicle_crop=vehicle_crop,
                vehicle_bbox=vehicle_bbox,
                frame_shape=frame_shape,
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


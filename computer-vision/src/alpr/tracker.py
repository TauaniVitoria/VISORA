"""
Módulo de rastreamento de veículos e prevenção de eventos duplicados.
Associa detecções entre quadros consecutivos por IoU e distância euclidiana de centroides,
consolida leituras de placas por confirmação temporal e aplica cooldown para evitar duplicidades.
"""

from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import numpy as np


@dataclass
class PlateObservation:
    """Observação individual de leitura de placa associada a um veículo rastreado."""
    frame_idx: int
    timestamp_sec: float
    plate: str
    pattern: str
    det_confidence: float
    ocr_confidence: float
    bbox: Tuple[int, int, int, int]


@dataclass
class ConfirmedPassageEvent:
    """Evento consolidado de passagem de veículo sem duplicidades."""
    track_id: int
    vehicle_class: str
    plate: str
    pattern: str
    det_confidence: float
    ocr_confidence: float
    first_frame_idx: int
    last_frame_idx: int
    timestamp_sec: float
    bbox_plate: Tuple[int, int, int, int]
    total_hits: int


class Track:
    """Representa a trajetória temporal de um veículo individual no campo de visão."""

    def __init__(self, track_id: int, bbox: Tuple[int, int, int, int], vehicle_class: str, frame_idx: int, timestamp_sec: float):
        self.track_id = track_id
        self.bbox = bbox
        self.vehicle_class = vehicle_class
        self.first_frame_idx = frame_idx
        self.last_frame_idx = frame_idx
        self.last_timestamp_sec = timestamp_sec
        self.disappeared_frames = 0
        self.event_emitted = False
        self.observations: List[PlateObservation] = []

    @property
    def centroid(self) -> Tuple[float, float]:
        """Calcula o centroide da bounding box atual."""
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)

    def add_observation(self, obs: PlateObservation) -> None:
        """Adiciona uma leitura de placa ao histórico da trajetória."""
        self.observations.append(obs)
        self.last_frame_idx = obs.frame_idx
        self.last_timestamp_sec = obs.timestamp_sec

    def update_bbox(self, bbox: Tuple[int, int, int, int], frame_idx: int, timestamp_sec: float) -> None:
        """Atualiza a posição do veículo no quadro corrente."""
        self.bbox = bbox
        self.last_frame_idx = frame_idx
        self.last_timestamp_sec = timestamp_sec
        self.disappeared_frames = 0

    def get_consolidated_plate(self) -> Optional[Tuple[str, str, float, float, Tuple[int, int, int, int]]]:
        """
        Consolida as leituras acumuladas através de votação por maioria ponderada
        pela confiança do OCR.

        Returns:
            Tupla (placa, padrao, det_conf, ocr_conf, bbox) ou None se não houver observações.
        """
        if not self.observations:
            return None

        # Agrupar observações por placa
        plate_scores: Dict[str, float] = {}
        plate_patterns: Dict[str, str] = {}
        plate_det_confs: Dict[str, List[float]] = {}
        plate_ocr_confs: Dict[str, List[float]] = {}
        plate_bboxes: Dict[str, Tuple[int, int, int, int]] = {}

        for obs in self.observations:
            p = obs.plate
            plate_scores[p] = plate_scores.get(p, 0.0) + (1.0 + obs.ocr_confidence)
            plate_patterns[p] = obs.pattern
            plate_det_confs.setdefault(p, []).append(obs.det_confidence)
            plate_ocr_confs.setdefault(p, []).append(obs.ocr_confidence)
            plate_bboxes[p] = obs.bbox

        # Escolhe a placa com maior pontuação agregada
        best_plate = max(plate_scores.items(), key=lambda item: item[1])[0]
        pattern = plate_patterns[best_plate]
        mean_det = float(np.mean(plate_det_confs[best_plate]))
        mean_ocr = float(np.mean(plate_ocr_confs[best_plate]))
        bbox = plate_bboxes[best_plate]

        return best_plate, pattern, mean_det, mean_ocr, bbox


class VehicleTracker:
    """
    Rastreador de veículos multicâmera/mono-câmera com prevenção de duplicidades.
    Evita emissão repetida de passagens durante a permanência de um mesmo veículo.
    """

    def __init__(
        self,
        iou_threshold: float = 0.3,
        max_disappeared_frames: int = 15,
        confirmation_hits: int = 3,
        cooldown_seconds: float = 10.0,
    ):
        self.iou_threshold = iou_threshold
        self.max_disappeared_frames = max_disappeared_frames
        self.confirmation_hits = confirmation_hits
        self.cooldown_seconds = cooldown_seconds

        self._next_track_id = 1
        self.tracks: Dict[int, Track] = {}
        # Histórico de emissões de placas para cooldown: placa -> último_timestamp_emissao
        self._plate_cooldown_history: Dict[str, float] = {}

    def reset(self) -> None:
        """Reinicia o estado interno do rastreador para reuso entre vídeos."""
        self._next_track_id = 1
        self.tracks.clear()
        self._plate_cooldown_history.clear()

    @staticmethod
    def compute_iou(box1: Tuple[int, int, int, int], box2: Tuple[int, int, int, int]) -> float:
        """Calcula a Intersection over Union (IoU) entre duas caixas."""
        x1_a, y1_a, x2_a, y2_a = box1
        x1_b, y1_b, x2_b, y2_b = box2

        xi1 = max(x1_a, x1_b)
        yi1 = max(y1_a, y1_b)
        xi2 = min(x2_a, x2_b)
        yi2 = min(y2_a, y2_b)

        inter_w = max(0, xi2 - xi1)
        inter_h = max(0, yi2 - yi1)
        inter_area = inter_w * inter_h

        area_a = (x2_a - x1_a) * (y2_a - y1_a)
        area_b = (x2_b - x1_b) * (y2_b - y1_b)
        union_area = area_a + area_b - inter_area

        if union_area <= 0:
            return 0.0

        return float(inter_area) / float(union_area)

    def update(
        self,
        vehicle_detections: List[Tuple[Tuple[int, int, int, int], str]],  # [(bbox, class_name), ...]
        plate_detections: List[PlateObservation],  # Leituras associadas aos veículos
        frame_idx: int,
        timestamp_sec: float,
    ) -> List[ConfirmedPassageEvent]:
        """
        Atualiza o estado dos tracks com as novas detecções do quadro e retorna
        eventos consolidados no quadro atual.

        Returns:
            Lista de ConfirmedPassageEvent disparados neste quadro.
        """
        new_confirmed_events: List[ConfirmedPassageEvent] = []

        # 1. Se não há tracks ativos, registra novos tracks para cada detecção
        if not self.tracks:
            for v_bbox, v_class in vehicle_detections:
                t = Track(self._next_track_id, v_bbox, v_class, frame_idx, timestamp_sec)
                self.tracks[self._next_track_id] = t
                self._next_track_id += 1
        else:
            # Associação de caixas existentes com as novas detecções via IoU
            track_ids = list(self.tracks.keys())
            matched_track_indices = set()
            matched_det_indices = set()

            if vehicle_detections:
                iou_matrix = np.zeros((len(track_ids), len(vehicle_detections)), dtype=np.float32)
                for i, tid in enumerate(track_ids):
                    for j, (v_bbox, _) in enumerate(vehicle_detections):
                        iou_matrix[i, j] = self.compute_iou(self.tracks[tid].bbox, v_bbox)

                # Associação gulosa pelas maiores IoUs
                while True:
                    if iou_matrix.size == 0 or np.max(iou_matrix) < self.iou_threshold:
                        break
                    max_idx = np.unravel_index(np.argmax(iou_matrix), iou_matrix.shape)
                    i, j = int(max_idx[0]), int(max_idx[1])

                    tid = track_ids[i]
                    v_bbox, _ = vehicle_detections[j]
                    self.tracks[tid].update_bbox(v_bbox, frame_idx, timestamp_sec)

                    matched_track_indices.add(i)
                    matched_det_indices.add(j)

                    # Zera linha e coluna selecionadas
                    iou_matrix[i, :] = -1.0
                    iou_matrix[:, j] = -1.0

            # Atualiza tracks que não deram match como desaparecidos
            for i, tid in enumerate(track_ids):
                if i not in matched_track_indices:
                    self.tracks[tid].disappeared_frames += 1

            # Cria novos tracks para detecções que não deram match
            for j, (v_bbox, v_class) in enumerate(vehicle_detections):
                if j not in matched_det_indices:
                    t = Track(self._next_track_id, v_bbox, v_class, frame_idx, timestamp_sec)
                    self.tracks[self._next_track_id] = t
                    self._next_track_id += 1

        # 2. Associa as observações de placas aos tracks mais próximos
        for obs in plate_detections:
            px1, py1, px2, py2 = obs.bbox
            pcx, pcy = (px1 + px2) / 2.0, (py1 + py2) / 2.0

            best_tid: Optional[int] = None
            best_dist = float("inf")

            for tid, track in self.tracks.items():
                vx1, vy1, vx2, vy2 = track.bbox
                # Verifica se a placa está dentro ou próxima da bounding box do veículo
                if vx1 <= pcx <= vx2 and vy1 <= pcy <= vy2:
                    dist = (track.centroid[0] - pcx) ** 2 + (track.centroid[1] - pcy) ** 2
                    if dist < best_dist:
                        best_dist = dist
                        best_tid = tid

            if best_tid is not None:
                self.tracks[best_tid].add_observation(obs)

        # 3. Avalia confirmação e regras de cooldown para evitar duplicidades
        for tid, track in list(self.tracks.items()):
            if not track.event_emitted and len(track.observations) >= self.confirmation_hits:
                consolidated = track.get_consolidated_plate()
                if consolidated is not None:
                    plate, pattern, det_conf, ocr_conf, bbox = consolidated

                    # Checar cooldown para esta placa
                    last_seen_time = self._plate_cooldown_history.get(plate, -float("inf"))
                    time_diff = timestamp_sec - last_seen_time

                    if time_diff >= self.cooldown_seconds:
                        event = ConfirmedPassageEvent(
                            track_id=track.track_id,
                            vehicle_class=track.vehicle_class,
                            plate=plate,
                            pattern=pattern,
                            det_confidence=det_conf,
                            ocr_confidence=ocr_conf,
                            first_frame_idx=track.first_frame_idx,
                            last_frame_idx=track.last_frame_idx,
                            timestamp_sec=timestamp_sec,
                            bbox_plate=bbox,
                            total_hits=len(track.observations),
                        )
                        new_confirmed_events.append(event)
                        track.event_emitted = True
                        self._plate_cooldown_history[plate] = timestamp_sec

        # 4. Remover tracks que excederam o limite de quadros desaparecidos
        dead_tracks = [tid for tid, t in self.tracks.items() if t.disappeared_frames > self.max_disappeared_frames]
        for tid in dead_tracks:
            del self.tracks[tid]

        return new_confirmed_events


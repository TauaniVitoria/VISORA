"""
Pipeline principal de visão computacional para Reconhecimento Automático de Placas (ALPR).
Orquestra aquisição de vídeo, detecção de veículos e placas, pré-processamento,
reconhecimento CRNN, validação regulatória, rastreamento temporal e exportação de resultados.
"""

import argparse
import csv
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np
import yaml

from alpr.image_preprocessor import ImagePreprocessor
from alpr.plate_detector import PlateDetector
from alpr.plate_recognizer import PlateRecognizer
from alpr.plate_validator import PlatePattern, PlateValidator
from alpr.tracker import ConfirmedPassageEvent, PlateObservation, VehicleTracker
from alpr.vehicle_detector import VehicleDetector
from alpr.video_reader import VideoReader
from alpr.visualizer import VideoWriterOutput, Visualizer


@dataclass
class FrameDetectionRecord:
    """Registro individual de detecção por quadro para auditoria e métricas."""
    frame_idx: int
    timestamp_sec: float
    vehicle_class: str
    track_id: Optional[int]
    plate: str
    pattern: str
    is_valid: bool
    det_confidence: float
    ocr_confidence: float
    bbox_vehicle: List[int]
    bbox_plate: List[int]


@dataclass
class PipelineMetrics:
    """Métricas consolidadas de desempenho e processamento do pipeline."""
    video_path: str
    total_frames_processed: int
    processing_time_seconds: float
    average_fps: float
    vehicles_detected_count: int
    plates_detected_count: int
    valid_plates_count: int
    invalid_plates_count: int
    confirmed_passages_count: int


class ALPRPipeline:
    """
    Pipeline orquestrador completo do sistema ALPR.
    """

    def __init__(self, config_path: str | Path):
        self.config_path = Path(config_path).resolve()
        self.config = self._load_config()
        self._init_components()

    def _load_config(self) -> Dict[str, Any]:
        """Carrega e valida o arquivo de configuração YAML."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Arquivo de configuração não encontrado: {self.config_path}")
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _init_components(self) -> None:
        """Inicializa todos os módulos do pipeline com base no YAML."""
        sys_cfg = self.config.get("system", {})
        veh_cfg = self.config.get("vehicle_detection", {})
        plt_cfg = self.config.get("plate_detection", {})
        prp_cfg = self.config.get("preprocessor", {})
        rec_cfg = self.config.get("plate_recognition", {})
        val_cfg = self.config.get("plate_validator", {})
        trk_cfg = self.config.get("tracker", {})
        vis_cfg = self.config.get("visualizer", {})

        device = sys_cfg.get("device", "auto")

        # 1. Detector de Veículos
        self.vehicle_detector = VehicleDetector(
            model_name=veh_cfg.get("model_name", "yolov8n.pt"),
            confidence_threshold=veh_cfg.get("confidence_threshold", 0.5),
            iou_threshold=veh_cfg.get("iou_threshold", 0.45),
            target_classes=veh_cfg.get("target_classes", [2, 3, 5, 7]),
            crop_padding_px=veh_cfg.get("crop_padding_px", 10),
            device=device,
        )

        # 2. Detector Especializado de Placas
        self.plate_detector = PlateDetector(
            model_path=plt_cfg.get("model_path", "models/weights/plate_detector_yolo.pt"),
            confidence_threshold=plt_cfg.get("confidence_threshold", 0.4),
            iou_threshold=plt_cfg.get("iou_threshold", 0.4),
            min_aspect_ratio=plt_cfg.get("min_aspect_ratio", 1.5),
            max_aspect_ratio=plt_cfg.get("max_aspect_ratio", 4.5),
            device=device,
        )

        # 3. Pré-processador de Imagens
        self.preprocessor = ImagePreprocessor(
            target_width=prp_cfg.get("target_width", 128),
            target_height=prp_cfg.get("target_height", 32),
            grayscale=prp_cfg.get("grayscale", True),
            normalize=prp_cfg.get("normalize", True),
            gaussian_blur=prp_cfg.get("gaussian_blur", {}).get("enabled", True),
            blur_kernel_size=tuple(prp_cfg.get("gaussian_blur", {}).get("kernel_size", [3, 3])),
            contrast_method=prp_cfg.get("contrast_adjustment", {}).get("method", "clahe"),
            clahe_clip_limit=prp_cfg.get("contrast_adjustment", {}).get("clip_limit", 2.0),
            clahe_tile_grid_size=tuple(prp_cfg.get("contrast_adjustment", {}).get("tile_grid_size", [8, 8])),
            binarization_enabled=prp_cfg.get("binarization", {}).get("enabled", False),
        )

        # 4. Reconhecedor de Caracteres (CRNN)
        self.plate_recognizer = PlateRecognizer(
            model_path=rec_cfg.get("model_path", "models/weights/crnn_plate_recognition.pth"),
            character_set=rec_cfg.get("character_set"),
            img_height=rec_cfg.get("img_height", 32),
            img_width=rec_cfg.get("img_width", 128),
            device=device,
            min_confidence=rec_cfg.get("min_ocr_confidence", 0.60),
        )

        # 5. Validador Regulatório de Placas
        self.plate_validator = PlateValidator(
            strip_special_chars=val_cfg.get("strip_special_chars", True),
        )

        # 6. Rastreador e Prevenção de Duplicidades
        self.tracker = VehicleTracker(
            iou_threshold=0.3,
            max_disappeared_frames=trk_cfg.get("max_disappeared_frames", 15),
            confirmation_hits=trk_cfg.get("confirmation_hits", 3),
            cooldown_seconds=trk_cfg.get("cooldown_seconds", 10.0),
        )

        # 7. Visualizador
        self.visualizer = Visualizer(
            vehicle_box_color=tuple(vis_cfg.get("vehicle_box_color", [0, 165, 255])),
            plate_box_color=tuple(vis_cfg.get("plate_box_color", [0, 255, 0])),
            font_scale=vis_cfg.get("font_scale", 0.6),
            bbox_thickness=vis_cfg.get("bbox_thickness", 2),
        )

    def process_video(
        self,
        video_path: str | Path,
        output_dir: Optional[str | Path] = None,
        max_frames: Optional[int] = None,
        save_video: Optional[bool] = None,
    ) -> Tuple[List[ConfirmedPassageEvent], PipelineMetrics]:
        """
        Executa o pipeline completo sobre um arquivo de vídeo.

        Args:
            video_path: Caminho do vídeo de entrada.
            output_dir: Diretório para exportação de dados e vídeo anotado.
            max_frames: Limite opcional de quadros para processar.
            save_video: Se deve gravar o vídeo anotado.

        Returns:
            Tupla contendo (eventos_confirmados, metricas_de_execucao).
        """
        v_path = Path(video_path).resolve()
        out_dir = Path(output_dir or self.config.get("video", {}).get("output_dir", "data/output")).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

        should_save_video = save_video if save_video is not None else self.config.get("system", {}).get("save_output_video", True)

        all_frame_records: List[FrameDetectionRecord] = []
        confirmed_passages: List[ConfirmedPassageEvent] = []

        total_vehicles_detected = 0
        total_plates_detected = 0
        total_valid_plates = 0
        total_invalid_plates = 0

        start_time = time.time()
        frames_processed = 0

        with VideoReader(v_path) as reader:
            metadata = reader.metadata
            video_writer: Optional[VideoWriterOutput] = None

            if should_save_video:
                output_video_path = out_dir / f"annotated_{v_path.stem}.mp4"
                video_writer = VideoWriterOutput(
                    output_path=output_video_path,
                    fps=metadata.fps,
                    frame_size=(metadata.width, metadata.height),
                )

            try:
                for v_frame in reader.read_frames(max_frames=max_frames):
                    frames_processed += 1
                    frame_img = v_frame.image.copy()

                    # 1. Detecção de Veículos
                    vehicle_dets = self.vehicle_detector.detect(v_frame.image)
                    total_vehicles_detected += len(vehicle_dets)

                    vehicle_tuples: List[Tuple[Tuple[int, int, int, int], str]] = []
                    frame_plate_obs: List[PlateObservation] = []

                    for v_det in vehicle_dets:
                        vehicle_tuples.append((v_det.bbox, v_det.class_name))

                        # 2. Detecção de Placas dentro da ROI do veículo
                        plates = self.plate_detector.detect_in_vehicle(
                            vehicle_crop=v_det.crop,
                            vehicle_bbox=v_det.bbox,
                            frame_shape=(metadata.height, metadata.width),
                        )
                        total_plates_detected += len(plates)

                        for p_det in plates:
                            # 3. Pré-processamento
                            preprocessed = self.preprocessor.process(p_det.crop)

                            # 4. OCR CRNN
                            rec_res = self.plate_recognizer.recognize(preprocessed.normalized)

                            # 5. Validação Regulamentar Brasileira
                            val_res = self.plate_validator.validate(rec_res.text)

                            if val_res.is_valid:
                                total_valid_plates += 1
                            else:
                                total_invalid_plates += 1

                            # Cria observação de placa
                            obs = PlateObservation(
                                frame_idx=v_frame.frame_idx,
                                timestamp_sec=v_frame.timestamp_seconds,
                                plate=val_res.normalized_plate,
                                pattern=val_res.pattern.value,
                                det_confidence=p_det.confidence,
                                ocr_confidence=rec_res.confidence,
                                bbox=p_det.bbox,
                            )
                            frame_plate_obs.append(obs)

                            all_frame_records.append(
                                FrameDetectionRecord(
                                    frame_idx=v_frame.frame_idx,
                                    timestamp_sec=v_frame.timestamp_seconds,
                                    vehicle_class=v_det.class_name,
                                    track_id=None,
                                    plate=val_res.normalized_plate,
                                    pattern=val_res.pattern.value,
                                    is_valid=val_res.is_valid,
                                    det_confidence=p_det.confidence,
                                    ocr_confidence=rec_res.confidence,
                                    bbox_vehicle=list(v_det.bbox),
                                    bbox_plate=list(p_det.bbox),
                                )
                            )

                            # Desenhar placa no visualizador
                            label = f"{val_res.normalized_plate}" if val_res.normalized_plate else "PLACA"
                            self.visualizer.draw_bbox_with_label(
                                image=frame_img,
                                bbox=p_det.bbox,
                                label=label,
                                color=self.visualizer.plate_box_color,
                                confidence=rec_res.confidence if rec_res.confidence > 0 else p_det.confidence,
                            )

                        # Desenhar veículo
                        self.visualizer.draw_bbox_with_label(
                            image=frame_img,
                            bbox=v_det.bbox,
                            label=v_det.class_name.upper(),
                            color=self.visualizer.vehicle_box_color,
                            confidence=v_det.confidence,
                        )

                    # 6. Rastreamento e Prevenção de Duplicidades
                    new_events = self.tracker.update(
                        vehicle_detections=vehicle_tuples,
                        plate_detections=frame_plate_obs,
                        frame_idx=v_frame.frame_idx,
                        timestamp_sec=v_frame.timestamp_seconds,
                    )
                    confirmed_passages.extend(new_events)

                    # 7. Telemetria e escrita do quadro
                    elapsed = time.time() - start_time
                    current_fps = (frames_processed / elapsed) if elapsed > 0 else 0.0
                    self.visualizer.draw_telemetry(
                        image=frame_img,
                        frame_idx=v_frame.frame_idx,
                        fps=current_fps,
                        active_tracks=len(self.tracker.tracks),
                        confirmed_plates=len(confirmed_passages),
                    )

                    if video_writer is not None:
                        video_writer.write_frame(frame_img)

            finally:
                if video_writer is not None:
                    video_writer.release()

        total_time = time.time() - start_time
        avg_fps = (frames_processed / total_time) if total_time > 0 else 0.0

        metrics = PipelineMetrics(
            video_path=str(v_path),
            total_frames_processed=frames_processed,
            processing_time_seconds=round(total_time, 3),
            average_fps=round(avg_fps, 2),
            vehicles_detected_count=total_vehicles_detected,
            plates_detected_count=total_plates_detected,
            valid_plates_count=total_valid_plates,
            invalid_plates_count=total_invalid_plates,
            confirmed_passages_count=len(confirmed_passages),
        )

        # 8. Exportação dos Resultados
        if self.config.get("system", {}).get("export_csv", True):
            self.export_csv(confirmed_passages, out_dir / f"passages_{v_path.stem}.csv")

        if self.config.get("system", {}).get("export_json", True):
            self.export_json(confirmed_passages, metrics, out_dir / f"summary_{v_path.stem}.json")

        return confirmed_passages, metrics

    def export_csv(self, events: List[ConfirmedPassageEvent], output_path: Path) -> None:
        """Exporta a lista de eventos confirmados em formato CSV."""
        fieldnames = [
            "track_id",
            "vehicle_class",
            "plate",
            "pattern",
            "det_confidence",
            "ocr_confidence",
            "first_frame_idx",
            "last_frame_idx",
            "timestamp_sec",
            "bbox_plate_x1",
            "bbox_plate_y1",
            "bbox_plate_x2",
            "bbox_plate_y2",
            "total_hits",
        ]

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for ev in events:
                row = {
                    "track_id": ev.track_id,
                    "vehicle_class": ev.vehicle_class,
                    "plate": ev.plate,
                    "pattern": ev.pattern,
                    "det_confidence": round(ev.det_confidence, 4),
                    "ocr_confidence": round(ev.ocr_confidence, 4),
                    "first_frame_idx": ev.first_frame_idx,
                    "last_frame_idx": ev.last_frame_idx,
                    "timestamp_sec": round(ev.timestamp_sec, 3),
                    "bbox_plate_x1": ev.bbox_plate[0],
                    "bbox_plate_y1": ev.bbox_plate[1],
                    "bbox_plate_x2": ev.bbox_plate[2],
                    "bbox_plate_y2": ev.bbox_plate[3],
                    "total_hits": ev.total_hits,
                }
                writer.writerow(row)

    def export_json(self, events: List[ConfirmedPassageEvent], metrics: PipelineMetrics, output_path: Path) -> None:
        """Exporta o resumo das métricas e passagens em formato JSON estruturado."""
        data = {
            "metrics": asdict(metrics),
            "events": [asdict(ev) for ev in events],
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


def main():
    """Interface de linha de comando para execução do pipeline ALPR."""
    parser = argparse.ArgumentParser(description="Pipeline ALPR para Reconhecimento de Placas em Vídeos.")
    parser.add_argument("--video", type=str, required=True, help="Caminho do arquivo de vídeo local.")
    parser.add_argument("--config", type=str, default="config/alpr_config.yaml", help="Caminho do arquivo YAML.")
    parser.add_argument("--output", type=str, default="data/output", help="Diretório de saída.")
    parser.add_argument("--max-frames", type=int, default=None, help="Limite de quadros a processar.")
    parser.add_argument("--no-save-video", action="store_true", help="Não gerar arquivo de vídeo anotado.")

    args = parser.parse_args()

    pipeline = ALPRPipeline(config_path=args.config)
    print(f"[*] Iniciando processamento do vídeo: {args.video}")
    events, metrics = pipeline.process_video(
        video_path=args.video,
        output_dir=args.output,
        max_frames=args.max_frames,
        save_video=not args.no_save_video,
    )

    print("\n[+] Processamento Concluído com Sucesso!")
    print(f"    - Quadros Processados: {metrics.total_frames_processed}")
    print(f"    - Tempo Total: {metrics.processing_time_seconds}s (Média: {metrics.average_fps} FPS)")
    print(f"    - Veículos Detectados: {metrics.vehicles_detected_count}")
    print(f"    - Placas Detectadas: {metrics.plates_detected_count}")
    print(f"    - Passagens Confirmadas: {metrics.confirmed_passages_count}")


if __name__ == "__main__":
    main()

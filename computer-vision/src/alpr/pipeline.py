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
from alpr.plate_detector import PlateDetection, PlateDetector
from alpr.plate_recognizer import PlateRecognizer
from alpr.plate_validator import PlatePattern, PlateValidator
from alpr.tracker import ConfirmedPassageEvent, PlateObservation, VehicleTracker
from alpr.vehicle_detector import VehicleDetection, VehicleDetector
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
    valid_crops_count: int = 0
    ocr_recognized_count: int = 0
    mean_vehicle_confidence: float = 0.0
    mean_plate_confidence: float = 0.0
    mean_ocr_confidence: float = 0.0


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

    def reset(self) -> None:
        """Reinicia o estado temporal do rastreador mantendo os modelos carregados em memória."""
        if hasattr(self, "tracker") and self.tracker is not None:
            self.tracker.reset()

    def process_video(
        self,
        video_path: str | Path,
        output_dir: Optional[str | Path] = None,
        max_frames: Optional[int] = None,
        save_video: Optional[bool] = None,
        diagnostic_dir: Optional[str | Path] = None,
    ) -> Tuple[List[ConfirmedPassageEvent], PipelineMetrics]:
        """
        Executa o pipeline completo sobre um arquivo de vídeo.

        Args:
            video_path: Caminho do vídeo de entrada.
            output_dir: Diretório para exportação de dados e vídeo anotado.
            max_frames: Limite opcional de quadros para processar.
            save_video: Se deve gravar o vídeo anotado.
            diagnostic_dir: Diretório opcional para salvar artefatos visuais das 8 etapas.

        Returns:
            Tupla contendo (eventos_confirmados, metricas_de_execucao).
        """
        self.reset()
        v_path = Path(video_path).resolve()
        out_dir = Path(output_dir or self.config.get("video", {}).get("output_dir", "data/output")).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

        diag_path: Optional[Path] = None
        if diagnostic_dir is not None:
            diag_path = Path(diagnostic_dir).resolve()
            diag_path.mkdir(parents=True, exist_ok=True)
        elif self.config.get("system", {}).get("debug", False):
            diag_path = out_dir / "diagnostics" / v_path.stem
            diag_path.mkdir(parents=True, exist_ok=True)

        should_save_video = save_video if save_video is not None else self.config.get("system", {}).get("save_output_video", True)

        all_frame_records: List[FrameDetectionRecord] = []
        confirmed_passages: List[ConfirmedPassageEvent] = []

        total_vehicles_detected = 0
        total_plates_detected = 0
        total_valid_crops = 0
        total_ocr_recognized = 0
        total_valid_plates = 0
        total_invalid_plates = 0

        veh_confs: List[float] = []
        plate_confs: List[float] = []
        ocr_confs: List[float] = []
        saved_diag_plates: set[str] = set()

        start_time = time.time()
        frames_processed = 0

        with VideoReader(v_path) as reader:
            metadata = reader.metadata
            video_writer: Optional[VideoWriterOutput] = None

            # Amostragem adaptativa para vídeos de alta taxa de quadros (>= 45 FPS) quando sem max_frames
            frame_stride = 1
            if max_frames is None and metadata.fps >= 45.0 and metadata.total_frames >= 120:
                frame_stride = max(1, int(round(metadata.fps / 20.0)))

            if should_save_video:
                output_video_path = out_dir / f"annotated_{v_path.stem}.mp4"
                video_writer = VideoWriterOutput(
                    output_path=output_video_path,
                    fps=metadata.fps / frame_stride,
                    frame_size=(metadata.width, metadata.height),
                )

            try:
                for v_frame in reader.read_frames(max_frames=max_frames):
                    if frame_stride > 1 and (v_frame.frame_idx % frame_stride != 0):
                        continue

                    frames_processed += 1
                    frame_img = v_frame.image.copy() if (video_writer is not None or diag_path is not None) else None

                    # 1. Detecção de Veículos
                    vehicle_dets = self.vehicle_detector.detect(v_frame.image)

                    # Fallback para quadros sintéticos ou câmeras focadas diretamente na placa
                    if not vehicle_dets and self.config.get("plate_detection", {}).get("fallback_to_vehicle_crop", True):
                        direct_plates = self.plate_detector.detect_in_frame(v_frame.image)
                        for dp in direct_plates:
                            px1, py1, px2, py2 = dp.bbox
                            pad_x = max(80, int((px2 - px1) * 1.0))
                            pad_y = max(80, int((py2 - py1) * 2.5))
                            vx1 = max(0, px1 - pad_x)
                            vy1 = max(0, py1 - pad_y)
                            vx2 = min(metadata.width, px2 + pad_x)
                            vy2 = min(metadata.height, py2 + pad_y)
                            vehicle_dets.append(
                                VehicleDetection(
                                    bbox=(vx1, vy1, vx2, vy2),
                                    confidence=dp.confidence,
                                    class_id=2,
                                    class_name="car",
                                    crop=v_frame.image[vy1:vy2, vx1:vx2].copy(),
                                )
                            )

                    total_vehicles_detected += len(vehicle_dets)

                    vehicle_tuples: List[Tuple[Tuple[int, int, int, int], str]] = []
                    frame_plate_obs: List[PlateObservation] = []

                    for v_det in vehicle_dets:
                        veh_confs.append(v_det.confidence)
                        vehicle_tuples.append((v_det.bbox, v_det.class_name))

                        # Verifica se este veículo já corresponde a um track confirmado (evita reprocessar OCR desnecessariamente)
                        already_confirmed_track = False
                        for trk in self.tracker.tracks.values():
                            if trk.event_emitted and (trk.bbox[3] - v_det.bbox[3] <= 120):
                                if self.tracker.compute_iou(trk.bbox, v_det.bbox) >= 0.35:
                                    already_confirmed_track = True
                                    break

                        if already_confirmed_track:
                            if frame_img is not None:
                                self.visualizer.draw_bbox_with_label(
                                    image=frame_img,
                                    bbox=v_det.bbox,
                                    label=v_det.class_name.upper(),
                                    color=self.visualizer.vehicle_box_color,
                                    confidence=v_det.confidence,
                                )
                            continue

                        # 2. Detecção de Placas dentro da ROI do veículo
                        plates = self.plate_detector.detect_in_vehicle(
                            vehicle_crop=v_det.crop,
                            vehicle_bbox=v_det.bbox,
                            frame_shape=(metadata.height, metadata.width),
                        )
                        total_plates_detected += len(plates)

                        for p_det in plates:
                            plate_confs.append(p_det.confidence)
                            if p_det.crop is not None and p_det.crop.size > 0:
                                total_valid_crops += 1

                            # 3. Pré-processamento
                            preprocessed = self.preprocessor.process(p_det.crop)

                            # 4. OCR Híbrido (CRNN + CTC / EasyOCR)
                            rec_res = self.plate_recognizer.recognize(
                                preprocessed.normalized,
                                raw_plate_crop=p_det.crop,
                            )
                            if rec_res.text:
                                total_ocr_recognized += 1
                                ocr_confs.append(rec_res.confidence)

                            # 5. Validação Regulamentar Brasileira com Desambiguação Posicional
                            val_res = self.plate_validator.validate_ocr(rec_res.text)

                            if val_res.is_valid:
                                total_valid_plates += 1
                                # Apenas leituras válidas nos padrões Mercosul/Antigo alimentam a confirmação temporal
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

                                # Exportação de diagnóstico visual por placa única (Etapas 1 a 8)
                                if diag_path is not None and val_res.normalized_plate not in saved_diag_plates:
                                    saved_diag_plates.add(val_res.normalized_plate)
                                    self._save_visual_diagnostics(
                                        diag_dir=diag_path,
                                        frame_idx=v_frame.frame_idx,
                                        raw_frame=v_frame.image,
                                        vehicle_det=v_det,
                                        plate_det=p_det,
                                        rec_res=rec_res,
                                        val_res=val_res,
                                    )
                            else:
                                total_invalid_plates += 1

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

                            # Desenhar placa no visualizador apenas quando gerar vídeo anotado
                            if frame_img is not None:
                                label = f"{val_res.normalized_plate}" if val_res.normalized_plate else "PLACA"
                                self.visualizer.draw_bbox_with_label(
                                    image=frame_img,
                                    bbox=p_det.bbox,
                                    label=label,
                                    color=self.visualizer.plate_box_color,
                                    confidence=rec_res.confidence if rec_res.confidence > 0 else p_det.confidence,
                                )

                        # Desenhar veículo apenas quando gerar vídeo anotado
                        if frame_img is not None:
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
                    if video_writer is not None and frame_img is not None:
                        elapsed = time.time() - start_time
                        current_fps = (frames_processed / elapsed) if elapsed > 0 else 0.0
                        self.visualizer.draw_telemetry(
                            image=frame_img,
                            frame_idx=v_frame.frame_idx,
                            fps=current_fps,
                            active_tracks=len(self.tracker.tracks),
                            confirmed_plates=len(confirmed_passages),
                        )
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
            valid_crops_count=total_valid_crops,
            ocr_recognized_count=total_ocr_recognized,
            mean_vehicle_confidence=round(float(np.mean(veh_confs)), 4) if veh_confs else 0.0,
            mean_plate_confidence=round(float(np.mean(plate_confs)), 4) if plate_confs else 0.0,
            mean_ocr_confidence=round(float(np.mean(ocr_confs)), 4) if ocr_confs else 0.0,
        )

        # 8. Exportação dos Resultados
        if self.config.get("system", {}).get("export_csv", True):
            self.export_csv(confirmed_passages, out_dir / f"passages_{v_path.stem}.csv")

        if self.config.get("system", {}).get("export_json", True):
            self.export_json(confirmed_passages, metrics, out_dir / f"summary_{v_path.stem}.json")

        return confirmed_passages, metrics

    def _save_visual_diagnostics(
        self,
        diag_dir: Path,
        frame_idx: int,
        raw_frame: np.ndarray,
        vehicle_det: VehicleDetection,
        plate_det: PlateDetection,
        rec_res: Any,
        val_res: Any,
    ) -> None:
        """
        Salva os 8 artefatos de inspeção visual intermediária da pipeline para diagnóstico:
        1. Frame original
        2. Frame com veículo detectado
        3. Recorte do veículo
        4. Frame com placa detectada
        5. Recorte da placa
        6. Variantes de pré-processamento
        7. Resultado do OCR
        8. Texto final validado
        """
        plate_dir = diag_dir / f"frame_{frame_idx:04d}_{val_res.normalized_plate}"
        plate_dir.mkdir(parents=True, exist_ok=True)

        # 1. Frame original
        cv2.imwrite(str(plate_dir / "01_frame_original.jpg"), raw_frame)

        # 2. Frame com veículo detectado
        veh_vis = raw_frame.copy()
        self.visualizer.draw_bbox_with_label(
            veh_vis, vehicle_det.bbox, vehicle_det.class_name.upper(), self.visualizer.vehicle_box_color, vehicle_det.confidence
        )
        cv2.imwrite(str(plate_dir / "02_frame_veiculo_detectado.jpg"), veh_vis)

        # 3. Veículo recortado
        cv2.imwrite(str(plate_dir / "03_veiculo_recortado.jpg"), vehicle_det.crop)

        # 4. Frame com placa detectada
        plate_vis = veh_vis.copy()
        self.visualizer.draw_bbox_with_label(
            plate_vis, plate_det.bbox, val_res.normalized_plate, self.visualizer.plate_box_color, plate_det.confidence
        )
        cv2.imwrite(str(plate_dir / "04_frame_placa_detectada.jpg"), plate_vis)

        # 5. Placa recortada
        cv2.imwrite(str(plate_dir / "05_placa_recortada.jpg"), plate_det.crop)

        # 6. Imagens após pré-processamento
        variants = self.preprocessor.generate_diagnostic_variants(plate_det.crop)
        for v_name, v_img in variants.items():
            cv2.imwrite(str(plate_dir / f"06_preprocess_{v_name}.jpg"), v_img)

        # 7 & 8. Resultados do OCR e Validação Final
        diag_meta = {
            "frame_idx": frame_idx,
            "vehicle": {
                "class": vehicle_det.class_name,
                "confidence": round(vehicle_det.confidence, 4),
                "bbox": list(vehicle_det.bbox),
            },
            "plate_detection": {
                "confidence": round(plate_det.confidence, 4),
                "bbox_global": list(plate_det.bbox),
                "bbox_local": list(plate_det.local_bbox),
                "aspect_ratio": round(plate_det.aspect_ratio, 3),
            },
            "ocr": {
                "raw_text": rec_res.raw_characters,
                "recognized_text": rec_res.text,
                "confidence": round(rec_res.confidence, 4),
                "model_used": getattr(rec_res, "model_used", "crnn_ctc"),
                "is_trained_weights": rec_res.is_trained_weights,
            },
            "validation": {
                "is_valid": val_res.is_valid,
                "normalized_plate": val_res.normalized_plate,
                "pattern": val_res.pattern.value,
                "error_message": val_res.error_message,
            },
        }
        with open(plate_dir / "07_08_ocr_and_validation.json", "w", encoding="utf-8") as f:
            json.dump(diag_meta, f, indent=2, ensure_ascii=False)

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

"""
ALPR (Automatic License Plate Recognition) Package.
Módulo modular de visão computacional para detecção de veículos,
localização de placas, pré-processamento, OCR por CRNN, validação e rastreamento.
"""

from alpr.video_reader import VideoReader, VideoMetadata, VideoFrame, VideoReaderError
from alpr.vehicle_detector import VehicleDetector, VehicleDetection
from alpr.plate_detector import PlateDetector, PlateDetection
from alpr.image_preprocessor import ImagePreprocessor, PreprocessedImage
from alpr.plate_recognizer import PlateRecognizer, CRNNNet, RecognitionResult
from alpr.plate_validator import PlateValidator, PlatePattern, ValidationResult
from alpr.tracker import VehicleTracker, Track, PlateObservation, ConfirmedPassageEvent
from alpr.visualizer import Visualizer, VideoWriterOutput
from alpr.pipeline import ALPRPipeline, PipelineMetrics, FrameDetectionRecord

__version__ = "0.2.0"

__all__ = [
    "VideoReader",
    "VideoMetadata",
    "VideoFrame",
    "VideoReaderError",
    "VehicleDetector",
    "VehicleDetection",
    "PlateDetector",
    "PlateDetection",
    "ImagePreprocessor",
    "PreprocessedImage",
    "PlateRecognizer",
    "CRNNNet",
    "RecognitionResult",
    "PlateValidator",
    "PlatePattern",
    "ValidationResult",
    "VehicleTracker",
    "Track",
    "PlateObservation",
    "ConfirmedPassageEvent",
    "Visualizer",
    "VideoWriterOutput",
    "ALPRPipeline",
    "PipelineMetrics",
    "FrameDetectionRecord",
]

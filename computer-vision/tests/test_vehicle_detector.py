"""
Testes unitários para o módulo VehicleDetector.
Valida inicialização, resolução de dispositivo, validação de recortes com padding e detecção.
"""

from unittest.mock import MagicMock, patch
import numpy as np
import pytest

from alpr.vehicle_detector import VehicleDetection, VehicleDetector


def test_vehicle_detector_init():
    """Valida inicialização com parâmetros padrão e resolução de dispositivo."""
    detector = VehicleDetector(confidence_threshold=0.6, crop_padding_px=15, device="cpu")
    assert detector.confidence_threshold == 0.6
    assert detector.crop_padding_px == 15
    assert detector.device == "cpu"
    assert detector.model is not None


def test_vehicle_detector_empty_frame():
    """Valida que quadros vazios ou nulos retornam lista vazia com segurança."""
    detector = VehicleDetector(device="cpu")
    assert detector.detect(np.array([])) == []
    assert detector.detect(None) == []  # type: ignore


def test_vehicle_detector_cropping_and_clamping():
    """Valida o recorte da ROI do veículo com padding e restrição de limites."""
    detector = VehicleDetector(crop_padding_px=10, device="cpu")

    # Mock do resultado da predição do YOLO
    fake_frame = np.zeros((300, 400, 3), dtype=np.uint8)

    # Criação de um mock para a estrutura do Ultralytics Results
    mock_box = MagicMock()
    mock_box.cls = [MagicMock(item=lambda: 2)]  # Classe 2 = car
    mock_box.conf = [MagicMock(item=lambda: 0.88)]
    # BBox: x1=50, y1=60, x2=150, y2=160
    mock_box.xyxy = [MagicMock(cpu=lambda: MagicMock(numpy=lambda: np.array([50.0, 60.0, 150.0, 160.0])))]

    mock_result = MagicMock()
    mock_result.boxes = [mock_box]

    with patch.object(detector.model, "predict", return_value=[mock_result]):
        dets = detector.detect(fake_frame)
        assert len(dets) == 1
        d = dets[0]
        assert d.class_id == 2
        assert d.class_name == "car"
        assert d.confidence == 0.88
        assert d.bbox == (50, 60, 150, 160)
        # Com padding de 10px: y de 50 a 170 (altura 120), x de 40 a 160 (largura 120)
        assert d.crop.shape == (120, 120, 3)


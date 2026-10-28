"""
Testes unitários para o módulo PlateDetector.
Valida verificação de disponibilidade de pesos, transformação de coordenadas locais para globais
e filtragem por aspect ratio de placas veiculares.
"""

from unittest.mock import MagicMock, patch
import numpy as np
import pytest

from alpr.plate_detector import PlateDetector


def test_plate_detector_weights_not_found():
    """Valida que ausência de pesos customizados não quebra o sistema e reporta is_model_available=False."""
    detector = PlateDetector(model_path="models/weights/arquivo_inexistente_de_pesos.pt", device="cpu")
    assert not detector.is_model_available
    assert detector.detect_in_frame(np.zeros((100, 100, 3), dtype=np.uint8)) == []


def test_plate_detector_coordinate_translation_and_aspect_ratio():
    """Valida a conversão de coordenadas da ROI do veículo para a imagem global e filtro de aspecto."""
    detector = PlateDetector(
        model_path="models/weights/fake_weights.pt",
        min_aspect_ratio=2.0,
        max_aspect_ratio=4.5,
        device="cpu",
    )
    detector.model = MagicMock()  # Simula modelo carregado

    # Imagem original de 1080x1920
    frame_h, frame_w = 1080, 1920
    # Veículo detectado em: vx1=200, vy1=300, vx2=600, vy2=700 (ROI: 400x400)
    vehicle_bbox = (200, 300, 600, 700)
    vehicle_crop = np.zeros((400, 400, 3), dtype=np.uint8)

    # Caixa 1 (Válida): Placa na ROI em lx1=50, ly1=250, lx2=200, ly2=300 (W=150, H=50 -> Ratio=3.0)
    box_valid = MagicMock()
    box_valid.conf = [MagicMock(item=lambda: 0.92)]
    box_valid.xyxy = [MagicMock(cpu=lambda: MagicMock(numpy=lambda: np.array([50.0, 250.0, 200.0, 300.0])))]

    # Caixa 2 (Inválida por proporção vertical): lx1=10, ly1=10, lx2=30, ly2=90 (W=20, H=80 -> Ratio=0.25)
    box_invalid_ratio = MagicMock()
    box_invalid_ratio.conf = [MagicMock(item=lambda: 0.85)]
    box_invalid_ratio.xyxy = [MagicMock(cpu=lambda: MagicMock(numpy=lambda: np.array([10.0, 10.0, 30.0, 90.0])))]

    mock_result = MagicMock()
    mock_result.boxes = [box_valid, box_invalid_ratio]

    detector.model.predict.return_value = [mock_result]

    dets = detector.detect_in_vehicle(
        vehicle_crop=vehicle_crop,
        vehicle_bbox=vehicle_bbox,
        frame_shape=(frame_h, frame_w),
    )

    # Apenas a caixa com ratio válido (3.0) deve ser retornada
    assert len(dets) == 1
    p = dets[0]
    assert p.aspect_ratio == 3.0
    assert p.confidence == 0.92
    assert p.local_bbox == (50, 250, 200, 300)

    # Coordenadas globais: vx1 + lx1 = 200 + 50 = 250; vy1 + ly1 = 300 + 250 = 550
    # vx1 + lx2 = 200 + 200 = 400; vy1 + ly2 = 300 + 300 = 600
    assert p.bbox == (250, 550, 400, 600)
    assert p.crop.shape == (50, 150, 3)

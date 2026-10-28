"""
Testes unitários para o módulo ImagePreprocessor.
Valida escala de cinza, equalização adaptativa (CLAHE), redução de ruído,
redimensionamento, normalização numérica e integridade da imagem original.
"""

import numpy as np
import pytest

from alpr.image_preprocessor import ImagePreprocessor


def test_image_preprocessor_invalid_input():
    """Valida que entradas vazias ou nulas disparam ValueError."""
    preprocessor = ImagePreprocessor()
    with pytest.raises(ValueError):
        preprocessor.process(np.array([]))


def test_image_preprocessor_standard_pipeline():
    """Valida o pipeline padrão com CLAHE, grayscale e normalização."""
    preprocessor = ImagePreprocessor(
        target_width=128,
        target_height=32,
        grayscale=True,
        normalize=True,
        gaussian_blur=True,
        contrast_method="clahe",
        binarization_enabled=False,
    )

    # Imagem simulada de placa: 60x180 em BGR
    fake_plate = np.random.randint(50, 200, (60, 180, 3), dtype=np.uint8)
    original_copy = fake_plate.copy()

    res = preprocessor.process(fake_plate)

    # Preservação estrita da imagem original
    assert np.array_equal(res.original, original_copy)

    # Dimensões da imagem processada
    assert res.processed.shape == (32, 128)
    assert res.target_size == (128, 32)

    # Array normalizado float32 no intervalo [0.0, 1.0]
    assert res.normalized.dtype == np.float32
    assert res.normalized.shape == (32, 128)
    assert res.normalized.min() >= 0.0
    assert res.normalized.max() <= 1.0


def test_image_preprocessor_with_binarization():
    """Valida o pipeline com binarização Otsu habilitada."""
    preprocessor = ImagePreprocessor(
        target_width=128,
        target_height=32,
        binarization_enabled=True,
    )
    fake_plate = np.random.randint(0, 255, (40, 120, 3), dtype=np.uint8)
    res = preprocessor.process(fake_plate)

    # Valores binários únicos após Otsu (0 e 255)
    unique_vals = set(np.unique(res.processed))
    assert unique_vals.issubset({0, 255})


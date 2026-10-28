"""
Módulo de pré-processamento de imagens de placas para OCR.
Implementa transformações em pipeline com preservação da imagem original,
incluindo escala de cinza, equalização adaptativa (CLAHE), redução de ruído e binarização.
"""

from dataclasses import dataclass
from typing import Optional, Tuple
import cv2
import numpy as np


@dataclass
class PreprocessedImage:
    """Encapsula a imagem original e o resultado processado."""
    original: np.ndarray          # Imagem original BGR sem alterações
    processed: np.ndarray         # Imagem processada (2D ou 3D)
    normalized: np.ndarray        # Array float32 normalizado [0, 1] pronto para o modelo
    target_size: Tuple[int, int]  # (width, height) final


class ImagePreprocessor:
    """
    Pipeline configurável de pré-processamento digital de imagens de placas.
    Melhora o contraste e a legibilidade dos caracteres mantendo a integridade da imagem.
    """

    def __init__(
        self,
        target_width: int = 128,
        target_height: int = 32,
        grayscale: bool = True,
        normalize: bool = True,
        gaussian_blur: bool = True,
        blur_kernel_size: Tuple[int, int] = (3, 3),
        contrast_method: str = "clahe",
        clahe_clip_limit: float = 2.0,
        clahe_tile_grid_size: Tuple[int, int] = (8, 8),
        binarization_enabled: bool = False,
    ):
        self.target_width = target_width
        self.target_height = target_height
        self.grayscale = grayscale
        self.normalize = normalize
        self.gaussian_blur = gaussian_blur
        self.blur_kernel_size = blur_kernel_size
        self.contrast_method = contrast_method.lower()
        self.clahe_clip_limit = clahe_clip_limit
        self.clahe_tile_grid_size = clahe_tile_grid_size
        self.binarization_enabled = binarization_enabled

        # Inicialização do objeto CLAHE
        self._clahe = cv2.createCLAHE(
            clipLimit=self.clahe_clip_limit,
            tileGridSize=self.clahe_tile_grid_size,
        )

    def process(self, image: np.ndarray) -> PreprocessedImage:
        """
        Executa o pipeline completo de pré-processamento.

        Args:
            image: Imagem de entrada (geralmente BGR).

        Returns:
            PreprocessedImage contendo a imagem original e a tratada.
        """
        if image is None or image.size == 0:
            raise ValueError("Imagem fornecida para pré-processamento é nula ou vazia.")

        original = image.copy()
        current = image.copy()

        # 1. Conversão para escala de cinza
        if self.grayscale and len(current.shape) == 3 and current.shape[2] == 3:
            current = cv2.cvtColor(current, cv2.COLOR_BGR2GRAY)

        # 2. Redimensionamento para o tamanho esperado pelo reconhecedor OCR
        current = cv2.resize(
            current,
            (self.target_width, self.target_height),
            interpolation=cv2.INTER_CUBIC if (current.shape[1] < self.target_width) else cv2.INTER_AREA,
        )

        # 3. Ajuste de contraste (CLAHE)
        if self.contrast_method == "clahe":
            if len(current.shape) == 2:
                current = self._clahe.apply(current)
            else:
                # Para imagem colorida, aplica no canal L do espaço LAB
                lab = cv2.cvtColor(current, cv2.COLOR_BGR2LAB)
                l, a, b = cv2.split(lab)
                cl = self._clahe.apply(l)
                limg = cv2.merge((cl, a, b))
                current = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

        # 4. Redução de ruído (filtro Gaussiano)
        if self.gaussian_blur:
            k = self.blur_kernel_size
            # Garantir dimensões ímpares para o kernel
            kx = k[0] if k[0] % 2 != 0 else k[0] + 1
            ky = k[1] if k[1] % 2 != 0 else k[1] + 1
            current = cv2.GaussianBlur(current, (kx, ky), 0)

        # 5. Binarização opcional (Otsu)
        if self.binarization_enabled and len(current.shape) == 2:
            _, current = cv2.threshold(current, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # 6. Normalização numérica [0.0, 1.0]
        if self.normalize:
            normalized = current.astype(np.float32) / 255.0
        else:
            normalized = current.astype(np.float32)

        return PreprocessedImage(
            original=original,
            processed=current,
            normalized=normalized,
            target_size=(self.target_width, self.target_height),
        )


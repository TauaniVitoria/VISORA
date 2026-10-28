"""
Módulo de validação e normalização de placas veiculares brasileiras.
Implementa regras estritas de expressões regulares para os padrões Mercosul e Antigo (cinza),
preservando o texto original e rejeitando substituições arbitrárias de caracteres.
"""

from dataclasses import dataclass
from enum import Enum
import re
from typing import Optional


class PlatePattern(str, Enum):
    """Padrões oficiais de placas veiculares no Brasil."""
    MERCOSUL = "mercosul"  # Formato ABC1D23 (Brasil/Mercosul)
    ANTIGO = "antigo"      # Formato ABC1234 (Modelo anterior cinza)
    INVALIDO = "invalido"  # Não compatível com os formatos regulamentados


@dataclass(frozen=True)
class ValidationResult:
    """Resultado estruturado da validação de uma placa."""
    is_valid: bool
    pattern: PlatePattern
    normalized_plate: str
    raw_text: str
    error_message: Optional[str] = None


class PlateValidator:
    """
    Validador de placas automotivas brasileiras.
    
    Aplica normalização estrutural sem realizar substituições ambíguas inventadas
    (por exemplo, sem forçar '8' para virar 'B' ou vice-versa).
    """

    # Regex para padrão Antigo: 3 letras maiúsculas seguidas de 4 dígitos
    REGEX_ANTIGO = re.compile(r"^[A-Z]{3}[0-9]{4}$")

    # Regex para padrão Mercosul: 3 letras, 1 dígito, 1 letra, 2 dígitos
    REGEX_MERCOSUL = re.compile(r"^[A-Z]{3}[0-9][A-Z][0-9]{2}$")

    def __init__(self, strip_special_chars: bool = True):
        self.strip_special_chars = strip_special_chars

    def normalize(self, raw_text: str) -> str:
        """
        Normaliza o texto eliminando espaços em branco, hífens, pontos e
        convertendo para caixa alta.

        Args:
            raw_text: Texto original extraído pelo OCR.

        Returns:
            String normalizada contendo apenas caracteres alfanuméricos em maiúsculas.
        """
        if not raw_text:
            return ""

        text = raw_text.strip().upper()

        if self.strip_special_chars:
            # Remove qualquer caractere que não seja letra (A-Z) ou número (0-9)
            text = re.sub(r"[^A-Z0-9]", "", text)

        return text

    def validate(self, raw_text: str) -> ValidationResult:
        """
        Valida se o texto corresponde aos formatos oficiais de placas do Brasil.

        Args:
            raw_text: Texto cru obtido da etapa de OCR.

        Returns:
            ValidationResult contendo validade, padrão identificado e justificativa se inválido.
        """
        if not raw_text or not raw_text.strip():
            return ValidationResult(
                is_valid=False,
                pattern=PlatePattern.INVALIDO,
                normalized_plate="",
                raw_text=raw_text or "",
                error_message="Texto de entrada vazio ou nulo.",
            )

        normalized = self.normalize(raw_text)

        # Placas brasileiras têm exatamente 7 caracteres alfanuméricos
        if len(normalized) != 7:
            return ValidationResult(
                is_valid=False,
                pattern=PlatePattern.INVALIDO,
                normalized_plate=normalized,
                raw_text=raw_text,
                error_message=f"Tamanho incompatível ({len(normalized)} caracteres; esperado 7).",
            )

        # 1. Teste de conformidade com o padrão Mercosul (ABC1D23)
        if self.REGEX_MERCOSUL.match(normalized):
            return ValidationResult(
                is_valid=True,
                pattern=PlatePattern.MERCOSUL,
                normalized_plate=normalized,
                raw_text=raw_text,
                error_message=None,
            )

        # 2. Teste de conformidade com o padrão Antigo (ABC1234)
        if self.REGEX_ANTIGO.match(normalized):
            return ValidationResult(
                is_valid=True,
                pattern=PlatePattern.ANTIGO,
                normalized_plate=normalized,
                raw_text=raw_text,
                error_message=None,
            )

        # Não corresponde a nenhum padrão oficial
        return ValidationResult(
            is_valid=False,
            pattern=PlatePattern.INVALIDO,
            normalized_plate=normalized,
            raw_text=raw_text,
            error_message="Sequência de caracteres não corresponde aos padrões Mercosul (ABC1D23) nem Antigo (ABC1234).",
        )

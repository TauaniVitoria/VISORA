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

    # Mapeamentos posicionais estritos para desambiguação de confusões ópticas do OCR
    DIGIT_TO_LETTER = {
        "0": "O",
        "1": "I",
        "2": "Z",
        "4": "A",
        "5": "S",
        "6": "G",
        "8": "B",
    }
    LETTER_TO_DIGIT = {
        "O": "0",
        "Q": "0",
        "D": "0",
        "I": "1",
        "L": "1",
        "T": "1",
        "Z": "2",
        "S": "5",
        "G": "6",
        "B": "8",
    }

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

    def _apply_positional_correction_7(self, candidate: str) -> Optional[str]:
        """
        Aplica correção de caracteres visualmente ambíguos (O/0, I/1, B/8, S/5, Z/2)
        respeitando estritamente a posição esperada no padrão brasileiro (LLLNLNN ou LLLNNNN).
        Limite máximo de 2 substituições posicionais para evitar falsos positivos.
        """
        if len(candidate) != 7:
            return None

        chars = list(candidate)
        subs = 0

        # Posições 0, 1, 2: obrigatoriamente LETRAS [A-Z]
        for pos in (0, 1, 2):
            ch = chars[pos]
            if ch.isdigit():
                mapped = self.DIGIT_TO_LETTER.get(ch)
                if not mapped:
                    return None
                chars[pos] = mapped
                subs += 1

        # Posição 3: obrigatoriamente DÍGITO [0-9]
        if chars[3].isalpha():
            mapped = self.LETTER_TO_DIGIT.get(chars[3])
            if not mapped:
                return None
            chars[3] = mapped
            subs += 1

        # Posição 4: pode ser LETRA (Mercosul) ou DÍGITO (Antigo) -> preserva como está se alfanumérico
        if not chars[4].isalnum():
            return None

        # Posições 5, 6: obrigatoriamente DÍGITOS [0-9]
        for pos in (5, 6):
            ch = chars[pos]
            if ch.isalpha():
                mapped = self.LETTER_TO_DIGIT.get(ch)
                if not mapped:
                    return None
                chars[pos] = mapped
                subs += 1

        if subs > 2:
            return None

        corrected = "".join(chars)
        if self.REGEX_MERCOSUL.match(corrected) or self.REGEX_ANTIGO.match(corrected):
            return corrected
        return None

    def validate_ocr(self, raw_text: str) -> ValidationResult:
        """
        Valida saída do OCR com suporte a desambiguação posicional brasileira e remoção
        de artefato de borda ('BR' lateral em placas Mercosul que gera 8 caracteres).
        """
        direct = self.validate(raw_text)
        if direct.is_valid:
            return direct

        normalized = self.normalize(raw_text)
        candidates_7 = []
        if len(normalized) == 7:
            candidates_7.append(normalized)
        elif len(normalized) == 8:
            # Borda esquerda "BR" em placas Mercosul frequentemente adiciona 1 letra inicial
            candidates_7.append(normalized[1:])
            candidates_7.append(normalized[:-1])

        for cand in candidates_7:
            res_cand = self.validate(cand)
            if res_cand.is_valid:
                return ValidationResult(
                    is_valid=True,
                    pattern=res_cand.pattern,
                    normalized_plate=res_cand.normalized_plate,
                    raw_text=raw_text,
                    error_message=None,
                )
            corrected = self._apply_positional_correction_7(cand)
            if corrected:
                res_corr = self.validate(corrected)
                if res_corr.is_valid:
                    return ValidationResult(
                        is_valid=True,
                        pattern=res_corr.pattern,
                        normalized_plate=res_corr.normalized_plate,
                        raw_text=raw_text,
                        error_message=None,
                    )

        return direct


"""
Testes unitários para o módulo PlateValidator.
Valida regras de conformidade para placas no padrão Mercosul e Antigo, normalização,
rejeição de sequências inválidas e ausência de substituições arbitrárias.
"""

import pytest

from alpr.plate_validator import PlatePattern, PlateValidator


@pytest.fixture
def validator() -> PlateValidator:
    return PlateValidator(strip_special_chars=True)


@pytest.mark.parametrize(
    "raw_input,expected_plate",
    [
        ("BRA2E19", "BRA2E19"),
        ("abc1d23", "ABC1D23"),
        ("RIO-2A18", "RIO2A18"),
        ("  xyz 9f88  ", "XYZ9F88"),
    ],
)
def test_valid_mercosul_plates(validator: PlateValidator, raw_input: str, expected_plate: str):
    """Valida o reconhecimento de placas oficiais no padrão Mercosul (ABC1D23)."""
    res = validator.validate(raw_input)
    assert res.is_valid
    assert res.pattern == PlatePattern.MERCOSUL
    assert res.normalized_plate == expected_plate
    assert res.raw_text == raw_input
    assert res.error_message is None


@pytest.mark.parametrize(
    "raw_input,expected_plate",
    [
        ("ABC1234", "ABC1234"),
        ("kgt-9082", "KGT9082"),
        (" SP 1234 ", "SP1234"),  # tamanho 6, será inválido!
        ("ABC-5678", "ABC5678"),
    ],
)
def test_valid_antigo_plates(validator: PlateValidator, raw_input: str, expected_plate: str):
    """Valida o reconhecimento de placas no padrão Antigo cinza (ABC1234)."""
    res = validator.validate(raw_input)
    if len(expected_plate) == 7:
        assert res.is_valid
        assert res.pattern == PlatePattern.ANTIGO
        assert res.normalized_plate == expected_plate
        assert res.error_message is None
    else:
        assert not res.is_valid


@pytest.mark.parametrize(
    "invalid_input",
    [
        "",
        "   ",
        "ABC123",        # 6 caracteres
        "ABC12345",      # 8 caracteres
        "123ABCD",       # ordem invertida
        "1234567",       # apenas números
        "ABCDEFG",       # apenas letras
        "AB12CD3",       # padrão não existente
    ],
)
def test_invalid_plates(validator: PlateValidator, invalid_input: str):
    """Valida a rejeição estrita de placas fora da norma com registro de erro."""
    res = validator.validate(invalid_input)
    assert not res.is_valid
    assert res.pattern == PlatePattern.INVALIDO
    assert res.error_message is not None


def test_no_arbitrary_character_substitution(validator: PlateValidator):
    """
    Garante que o validador NÃO realiza substituições arbitrárias de caracteres ambíguos.
    Por exemplo, 'AB81D23' (com '8' no lugar da 3ª letra) não deve ser arbitrariamente alterado para 'B'.
    """
    res = validator.validate("AB81D23")
    assert not res.is_valid
    # Mantém o '8' original sem inventar 'B'
    assert res.normalized_plate == "AB81D23"
    assert "não corresponde aos padrões" in res.error_message

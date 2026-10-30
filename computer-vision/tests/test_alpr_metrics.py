"""
Testes unitários para o módulo de métricas e avaliação de OCR / ALPR.
"""

from alpr.metrics import ALPRMetricsCalculator


def test_character_error_rate_exact_match():
    cer = ALPRMetricsCalculator.character_error_rate("BRA2E19", "BRA2E19")
    assert cer == 0.0


def test_character_error_rate_one_char_diff():
    # 1 caractere trocado em 7
    cer = ALPRMetricsCalculator.character_error_rate("BRA2E19", "BRA2E18")
    assert 0.14 <= cer <= 0.15


def test_character_error_rate_empty():
    assert ALPRMetricsCalculator.character_error_rate("", "") == 0.0
    assert ALPRMetricsCalculator.character_error_rate("ABC", "") == 1.0


def test_alpr_evaluation_metrics():
    ground_truth = ["BRA2E19", "RIO2A18", "ABC1234", "XYZ9999"]
    predictions = ["BRA2E19", "RIO2A18", "ABC1235", "XYZ9999", "BRA2E19"]

    metrics = ALPRMetricsCalculator.evaluate(ground_truth, predictions)

    assert metrics.total_ground_truth_samples == 4
    assert metrics.total_predictions == 5
    assert metrics.true_positives == 3  # BRA2E19, RIO2A18, XYZ9999 casam nos índices
    assert metrics.duplicate_count == 1  # BRA2E19 repetiu
    assert metrics.precision > 0.5
    assert metrics.recall > 0.5
    assert metrics.character_accuracy > 0.8


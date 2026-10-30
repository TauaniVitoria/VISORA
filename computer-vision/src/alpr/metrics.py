"""
Módulo de avaliação de métricas e benchmarking do sistema ALPR.
Permite calcular precisão, revocação, F1-score, taxa de erro de OCR (CER/WER),
duplicidades e tempo médio de processamento por quadro.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class ALPREvaluationMetrics:
    """Métricas quantitativas consolidadas de avaliação do pipeline ALPR."""
    total_ground_truth_samples: int
    total_predictions: int
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float
    character_accuracy: float
    exact_match_ratio: float
    duplicate_count: int
    unrecognized_plates_count: int


class ALPRMetricsCalculator:
    """
    Calculadora de métricas de acurácia, erros e duplicidades para ALPR.
    Permite comparar anotações reais (Ground Truth) com predições do pipeline.
    """

    @staticmethod
    def character_error_rate(reference: str, hypothesis: str) -> float:
        """
        Calcula a taxa de erro de caracteres (CER) via distância de Levenshtein normalizada.
        Retorna valor entre 0.0 (perfeito) e 1.0 (totalmente incorreto).
        """
        ref = reference.strip().upper()
        hyp = hypothesis.strip().upper()

        if not ref and not hyp:
            return 0.0
        if not ref:
            return 1.0

        # Algoritmo de distância de Levenshtein
        dp = [[0] * (len(hyp) + 1) for _ in range(len(ref) + 1)]
        for i in range(len(ref) + 1):
            dp[i][0] = i
        for j in range(len(hyp) + 1):
            dp[0][j] = j

        for i in range(1, len(ref) + 1):
            for j in range(1, len(hyp) + 1):
                cost = 0 if ref[i - 1] == hyp[j - 1] else 1
                dp[i][j] = min(
                    dp[i - 1][j] + 1,       # Deleção
                    dp[i][j - 1] + 1,       # Inserção
                    dp[i - 1][j - 1] + cost # Substituição
                )

        dist = dp[len(ref)][len(hyp)]
        return min(1.0, dist / max(len(ref), len(hyp)))

    @classmethod
    def evaluate(
        cls,
        ground_truth: List[str],
        predictions: List[str],
    ) -> ALPREvaluationMetrics:
        """
        Avalia listas pareadas de placas reais e placas preditas.
        
        Args:
            ground_truth: Lista de placas verdadeiras (anotadas).
            predictions: Lista de placas identificadas pelo modelo.
        """
        gt_norm = [p.strip().upper().replace("-", "") for p in ground_truth if p]
        pred_norm = [p.strip().upper().replace("-", "") for p in predictions if p]

        total_gt = len(gt_norm)
        total_pred = len(pred_norm)

        # Contagem de duplicados nas predições
        seen_preds: Set[str] = set()
        duplicate_count = 0
        for p in pred_norm:
            if p in seen_preds:
                duplicate_count += 1
            else:
                seen_preds.add(p)

        # Comparação por correspondência exata
        tp = 0
        unrecognized = 0
        total_cer = 0.0
        n_pairs = min(total_gt, total_pred)

        for i in range(n_pairs):
            gt = gt_norm[i]
            pred = pred_norm[i]

            if not pred or pred == "INVALIDO":
                unrecognized += 1

            if gt == pred:
                tp += 1

            total_cer += cls.character_error_rate(gt, pred)

        fp = max(0, total_pred - tp)
        fn = max(0, total_gt - tp)

        precision = (tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        recall = (tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

        avg_cer = (total_cer / n_pairs) if n_pairs > 0 else 0.0
        char_accuracy = max(0.0, 1.0 - avg_cer)
        exact_match = (tp / total_gt) if total_gt > 0 else 0.0

        return ALPREvaluationMetrics(
            total_ground_truth_samples=total_gt,
            total_predictions=total_pred,
            true_positives=tp,
            false_positives=fp,
            false_negatives=fn,
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1_score=round(f1, 4),
            character_accuracy=round(char_accuracy, 4),
            exact_match_ratio=round(exact_match, 4),
            duplicate_count=duplicate_count,
            unrecognized_plates_count=unrecognized,
        )

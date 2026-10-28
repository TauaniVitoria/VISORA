"""
Testes unitários para o módulo VehicleTracker.
Valida cálculo de IoU, rastreamento temporal de veículos, consolidação de leituras de placas,
exigência de confirmation_hits e mecanismo de cooldown para prevenção de duplicidades.
"""

import pytest

from alpr.tracker import PlateObservation, VehicleTracker


def test_compute_iou():
    """Valida o cálculo de interseção sobre união."""
    box_a = (0, 0, 10, 10)
    box_b = (0, 0, 10, 10)
    box_c = (10, 10, 20, 20)  # Sem sobreposição
    box_d = (5, 0, 15, 10)    # 50% de sobreposição horizontal

    assert VehicleTracker.compute_iou(box_a, box_b) == 1.0
    assert VehicleTracker.compute_iou(box_a, box_c) == 0.0
    assert abs(VehicleTracker.compute_iou(box_a, box_d) - (50.0 / 150.0)) < 1e-4


def test_tracker_confirmation_hits_and_cooldown():
    """Valida que são necessárias confirmation_hits leituras para disparar e que o cooldown impede duplicidades."""
    tracker = VehicleTracker(
        iou_threshold=0.3,
        confirmation_hits=3,
        cooldown_seconds=10.0,
    )

    # Frame 1: Veículo detectado com 1ª leitura de placa
    v_det = [((100, 100, 300, 300), "car")]
    p_obs_1 = [
        PlateObservation(
            frame_idx=1,
            timestamp_sec=0.1,
            plate="BRA2E19",
            pattern="mercosul",
            det_confidence=0.9,
            ocr_confidence=0.95,
            bbox=(180, 220, 240, 250),
        )
    ]
    events_f1 = tracker.update(v_det, p_obs_1, frame_idx=1, timestamp_sec=0.1)
    # Apenas 1 hit: ainda não atinge o limiar de 3 hits
    assert len(events_f1) == 0
    assert len(tracker.tracks) == 1

    # Frame 2: Veículo se move levemente, 2ª leitura
    v_det_2 = [((105, 100, 305, 300), "car")]
    p_obs_2 = [
        PlateObservation(
            frame_idx=2,
            timestamp_sec=0.2,
            plate="BRA2E19",
            pattern="mercosul",
            det_confidence=0.91,
            ocr_confidence=0.96,
            bbox=(185, 220, 245, 250),
        )
    ]
    events_f2 = tracker.update(v_det_2, p_obs_2, frame_idx=2, timestamp_sec=0.2)
    assert len(events_f2) == 0  # 2 hits: ainda não dispara

    # Frame 3: 3ª leitura consistente
    v_det_3 = [((110, 100, 310, 300), "car")]
    p_obs_3 = [
        PlateObservation(
            frame_idx=3,
            timestamp_sec=0.3,
            plate="BRA2E19",
            pattern="mercosul",
            det_confidence=0.92,
            ocr_confidence=0.97,
            bbox=(190, 220, 250, 250),
        )
    ]
    events_f3 = tracker.update(v_det_3, p_obs_3, frame_idx=3, timestamp_sec=0.3)
    # 3 hits atingidos: dispara exatamente 1 evento confirmado!
    assert len(events_f3) == 1
    ev = events_f3[0]
    assert ev.plate == "BRA2E19"
    assert ev.pattern == "mercosul"
    assert ev.vehicle_class == "car"
    assert ev.total_hits == 3

    # Frame 4: Mesmo veículo continua na cena (Frame 4)
    v_det_4 = [((115, 100, 315, 300), "car")]
    p_obs_4 = [
        PlateObservation(
            frame_idx=4,
            timestamp_sec=0.4,
            plate="BRA2E19",
            pattern="mercosul",
            det_confidence=0.92,
            ocr_confidence=0.97,
            bbox=(195, 220, 255, 250),
        )
    ]
    events_f4 = tracker.update(v_det_4, p_obs_4, frame_idx=4, timestamp_sec=0.4)
    # NÃO deve gerar evento duplicado para a mesma passagem!
    assert len(events_f4) == 0


def test_tracker_removes_dead_tracks():
    """Valida a limpeza de tracks após max_disappeared_frames sem detecção."""
    tracker = VehicleTracker(max_disappeared_frames=2)
    # Inicializa com 1 veículo
    tracker.update([((10, 10, 50, 50), "car")], [], frame_idx=1, timestamp_sec=0.0)
    assert len(tracker.tracks) == 1

    # 1º quadro sem detecção
    tracker.update([], [], frame_idx=2, timestamp_sec=0.1)
    assert len(tracker.tracks) == 1

    # 2º quadro sem detecção
    tracker.update([], [], frame_idx=3, timestamp_sec=0.2)
    assert len(tracker.tracks) == 1

    # 3º quadro sem detecção (excedeu max_disappeared_frames = 2)
    tracker.update([], [], frame_idx=4, timestamp_sec=0.3)
    assert len(tracker.tracks) == 0


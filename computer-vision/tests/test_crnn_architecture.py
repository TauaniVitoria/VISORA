"""
Testes unitários para a arquitetura CRNN e algoritmo de decodificação CTC Greedy.
Valida dimensões de tensores da CNN+BiLSTM, eliminação de blanks e repetições consecutivas.
"""

import numpy as np
import pytest
import torch

from alpr.plate_recognizer import CRNNNet, PlateRecognizer


def test_crnn_net_tensor_shapes():
    """Valida as dimensões dos tensores de entrada e saída da arquitetura CRNN."""
    num_classes = 37  # 1 blank + 36 caracteres alfanuméricos
    model = CRNNNet(img_channels=1, num_classes=num_classes, lstm_hidden=128)
    model.eval()

    batch_size = 2
    # Tensor de entrada: [Batch=2, Canais=1, Altura=32, Largura=128]
    dummy_input = torch.randn(batch_size, 1, 32, 128)

    with torch.no_grad():
        output = model(dummy_input)

    # Formato de saída esperado para PyTorch CTC Loss: [Seq_Len=31, Batch=2, Num_Classes=37]
    assert output.shape == (31, batch_size, num_classes)


def test_ctc_greedy_decoder():
    """Valida a decodificação CTC Greedy (colapso de repetições consecutivas e remoção de blanks)."""
    recognizer = PlateRecognizer(device="cpu")
    num_classes = recognizer.num_classes

    # Monta uma matriz simulada de logits [T=7, B=1, num_classes]
    # Índices desejados: Blank(0), 'A'(char_to_idx['A']), 'A', Blank(0), '1'(char_to_idx['1']), Blank(0)
    idx_a = recognizer.char_to_idx["A"]
    idx_1 = recognizer.char_to_idx["1"]
    blank = recognizer.blank_idx  # 0

    seq_indices = [blank, idx_a, idx_a, blank, idx_1, idx_1, blank]
    timesteps = len(seq_indices)

    logits = torch.full((timesteps, 1, num_classes), fill_value=-10.0)
    for t, char_idx in enumerate(seq_indices):
        logits[t, 0, char_idx] = 10.0  # Alta probabilidade para o token alvo

    decoded_text, confidence = recognizer.decode_ctc_greedy(logits)

    # 'A' duplicado consecutivo colapsa em 'A', seguido de '1' duplicado colapsando em '1'
    assert decoded_text == "A1"
    assert confidence > 0.95


def test_plate_recognizer_untrained_weights_mode():
    """Valida que o reconhecedor sem pesos carregados informa is_trained_weights=False."""
    recognizer = PlateRecognizer(model_path="caminho_inexistente.pth", device="cpu")
    assert not recognizer.is_weights_loaded

    fake_input = np.zeros((32, 128), dtype=np.float32)
    res = recognizer.recognize(fake_input)
    assert not res.is_trained_weights
    assert isinstance(res.text, str)

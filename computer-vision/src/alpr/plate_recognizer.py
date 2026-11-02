"""
Módulo de reconhecimento de caracteres em placas veiculares utilizando CRNN e PyTorch.
Implementa a arquitetura CNN + BiLSTM + Decodificador CTC Greedy para decodificação
de placas brasileiras (alfabeto alfanumérico A-Z e 0-9).
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple
import cv2
import numpy as np
import torch
import torch.nn as pd_nn
import torch.nn as nn
import torch.nn.functional as F


@dataclass
class RecognitionResult:
    """Resultado estruturado do reconhecimento óptico de caracteres (OCR)."""
    text: str                # Texto reconhecido decodificado
    confidence: float        # Confiança estimada [0.0, 1.0]
    raw_characters: str      # Sequência antes de pós-processamento
    is_trained_weights: bool # True se foi inferido com pesos treinados carregados
    model_used: str = "crnn_ctc"


class CRNNNet(nn.Module):
    """
    Arquitetura de Rede Neural Convolucional Recorrente (CRNN).
    Combina uma CNN para extração de mapas de características visuais e um
    Bi-LSTM de duas camadas para modelagem sequencial de dependências de caracteres.
    """

    def __init__(self, img_channels: int, num_classes: int, lstm_hidden: int = 256):
        super().__init__()

        # Camadas Convolucionais (VGG-style)
        self.cnn = nn.Sequential(
            # Bloco 1: [B, C, 32, 128] -> [B, 64, 16, 64]
            nn.Conv2d(img_channels, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),

            # Bloco 2: [B, 64, 16, 64] -> [B, 128, 8, 32]
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),

            # Bloco 3: [B, 128, 8, 32] -> [B, 256, 4, 32]
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.Conv2d(256, 256, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=(2, 1), stride=(2, 1)),

            # Bloco 4: [B, 256, 4, 32] -> [B, 512, 2, 32]
            nn.Conv2d(256, 512, kernel_size=3, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True),
            nn.Conv2d(512, 512, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=(2, 1), stride=(2, 1)),

            # Bloco 5: [B, 512, 2, 32] -> [B, 512, 1, 31]
            nn.Conv2d(512, 512, kernel_size=(2, 2), stride=(1, 1), padding=0),
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True),
        )

        # Camada Recorrente Bidirecional (2 camadas de Bi-LSTM)
        self.rnn = nn.LSTM(
            input_size=512,
            hidden_size=lstm_hidden,
            bidirectional=True,
            num_layers=2,
            batch_first=False,
        )

        # Projeção linear para as classes (alfabeto + blank token)
        self.fc = nn.Linear(lstm_hidden * 2, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Executa a passagem para frente da CRNN.

        Args:
            x: Tensor com shape [B, C, H=32, W=128]

        Returns:
            Logits de saída com shape [T, B, num_classes]
        """
        features = self.cnn(x)  # [B, 512, 1, W_seq]
        b, c, h, w_seq = features.size()
        assert h == 1, f"Altura da feature map deve ser 1 após CNN, obtido {h}"

        # Ajusta para formato de sequência temporal: [T=W_seq, B, C]
        features = features.squeeze(2).permute(2, 0, 1)

        # Passagem pela RNN
        recurrent_out, _ = self.rnn(features)  # [T, B, 2 * hidden]

        # Classificação por timestep
        logits = self.fc(recurrent_out)  # [T, B, num_classes]
        return logits


class PlateRecognizer:
    """
    Controlador do modelo CRNN para reconhecimento óptico de caracteres em placas.
    Prepara entradas, gerencia inferência no dispositivo alvo e aplica CTC Greedy Decoding.
    """

    DEFAULT_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def __init__(
        self,
        model_path: str = "models/weights/crnn_plate_recognition.pth",
        character_set: Optional[str] = None,
        img_height: int = 32,
        img_width: int = 128,
        device: str = "auto",
        min_confidence: float = 0.60,
    ):
        self.model_path = Path(model_path)
        self.character_set = character_set or self.DEFAULT_ALPHABET
        self.img_height = img_height
        self.img_width = img_width
        self.min_confidence = min_confidence
        self.device = self._resolve_device(device)

        # Mapeamento de caracteres: índice 0 é reservado para o CTC Blank Token
        self.blank_idx = 0
        self.idx_to_char = {idx + 1: char for idx, char in enumerate(self.character_set)}
        self.char_to_idx = {char: idx + 1 for idx, char in enumerate(self.character_set)}
        self.num_classes = len(self.character_set) + 1

        self.model = CRNNNet(img_channels=1, num_classes=self.num_classes)
        self.is_weights_loaded = False
        self._easyocr_reader = None
        self._load_weights_if_available()
        self.model.to(self.device)
        self.model.eval()

    def _get_easyocr_reader(self):
        """Inicializa sob demanda o leitor EasyOCR como motor secundário de confirmação."""
        if self._easyocr_reader is None:
            try:
                import easyocr
                self._easyocr_reader = easyocr.Reader(["en"], gpu=False, verbose=False)
            except Exception:
                self._easyocr_reader = False
        return self._easyocr_reader if self._easyocr_reader is not False else None

    def _resolve_device(self, requested_device: str) -> torch.device:
        """Resolve o torch.device apropriado (mps, cuda ou cpu)."""
        if requested_device == "auto":
            if torch.backends.mps.is_available():
                return torch.device("mps")
            elif torch.cuda.is_available():
                return torch.device("cuda")
            return torch.device("cpu")
        return torch.device(requested_device)

    def _load_weights_if_available(self) -> None:
        """Carrega os pesos pré-treinados do modelo se disponíveis em disco."""
        candidate = self.model_path
        if not candidate.exists() and str(self.model_path) == "models/weights/crnn_plate_recognition.pth":
            cv_root_candidate = Path(__file__).resolve().parents[2] / self.model_path
            if cv_root_candidate.exists():
                candidate = cv_root_candidate
                self.model_path = candidate

        if candidate.exists() and candidate.is_file():
            try:
                state_dict = torch.load(candidate, map_location=self.device)
                self.model.load_state_dict(state_dict)
                self.is_weights_loaded = True
            except Exception as e:
                self.is_weights_loaded = False
        else:
            self.is_weights_loaded = False

    def decode_ctc_greedy(self, logits: torch.Tensor) -> Tuple[str, float]:
        """
        Decodifica a saída da CRNN utilizando o algoritmo CTC Greedy.

        Args:
            logits: Tensor de shape [T, B=1, num_classes]

        Returns:
            Tupla (texto_decodificado, confianca_media)
        """
        probs = F.softmax(logits, dim=2)  # [T, 1, num_classes]
        max_probs, argmaxes = torch.max(probs, dim=2)  # [T, 1]

        argmaxes = argmaxes.squeeze(1).cpu().numpy()
        max_probs = max_probs.squeeze(1).cpu().numpy()

        decoded_chars: List[str] = []
        char_confidences: List[float] = []

        prev_idx = self.blank_idx

        for t in range(len(argmaxes)):
            idx = int(argmaxes[t])
            # Se for diferente do anterior e não for blank, emite o caractere
            if idx != prev_idx and idx != self.blank_idx:
                char = self.idx_to_char.get(idx, "")
                if char:
                    decoded_chars.append(char)
                    char_confidences.append(float(max_probs[t]))
            prev_idx = idx

        text = "".join(decoded_chars)
        confidence = float(np.mean(char_confidences)) if char_confidences else 0.0

        return text, confidence

    def recognize(
        self,
        preprocessed_image: np.ndarray,
        raw_plate_crop: Optional[np.ndarray] = None,
    ) -> RecognitionResult:
        """
        Executa a inferência OCR na imagem pré-processada de uma placa.
        Utiliza CRNN + CTC como motor primário e EasyOCR como confirmação secundária
        quando necessário em recortes reais.

        Args:
            preprocessed_image: Array numpy float32 normalizado com shape (H=32, W=128)
                                ou imagem BGR/Grayscale.
            raw_plate_crop: Recorte BGR/Grayscale original da placa para fallback EasyOCR.

        Returns:
            RecognitionResult com texto, confiança e metadados.
        """
        if preprocessed_image is None or preprocessed_image.size == 0:
            return RecognitionResult(text="", confidence=0.0, raw_characters="", is_trained_weights=self.is_weights_loaded)

        img = preprocessed_image

        # Se for imagem colorida, converter para escala de cinza
        if len(img.shape) == 3 and img.shape[2] == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Ajuste de dimensões caso necessário
        if img.shape[0] != self.img_height or img.shape[1] != self.img_width:
            img = cv2.resize(img, (self.img_width, self.img_height), interpolation=cv2.INTER_AREA)

        # Garantir normalização float32 [0.0, 1.0]
        if img.dtype != np.float32 or float(img.max()) > 1.5:
            img = img.astype(np.float32) / 255.0

        # Normalização padrão z-score (média 0.5, desvio 0.5)
        tensor = torch.from_numpy(img).unsqueeze(0).unsqueeze(0)  # [1, 1, 32, 128]
        tensor = (tensor - 0.5) / 0.5
        tensor = tensor.to(self.device)

        with torch.no_grad():
            logits = self.model(tensor)
            decoded_text, confidence = self.decode_ctc_greedy(logits)

        # Se não houver pesos carregados, documenta que os pesos não foram fornecidos
        if not self.is_weights_loaded:
            return RecognitionResult(
                text=decoded_text,
                confidence=confidence,
                raw_characters=decoded_text,
                is_trained_weights=False,
                model_used="crnn_ctc_untrained",
            )

        # Se a CRNN treinada já decodificou 7 caracteres com altíssima confiança (>= 0.92), retorna imediatamente
        if len(decoded_text) == 7 and confidence >= 0.92:
            return RecognitionResult(
                text=decoded_text,
                confidence=round(confidence, 4),
                raw_characters=decoded_text,
                is_trained_weights=True,
                model_used="crnn_ctc",
            )

        # Motor híbrido CRNN + EasyOCR quando a confiança da CRNN é < 0.92 ou tamanho != 7:
        # EasyOCR verifica a presença real de caracteres na placa (evitando alucinações em regiões sem texto),
        # enquanto a CRNN refina leituras parcialmente borradas/sombreadas que compartilham estrutura com o texto lido.
        if raw_plate_crop is not None and raw_plate_crop.size > 0:
            reader = self._get_easyocr_reader()
            if reader is not None:
                try:
                    up = cv2.resize(raw_plate_crop, (0, 0), fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC)
                    gray_up = cv2.cvtColor(up, cv2.COLOR_BGR2GRAY) if len(up.shape) == 3 else up
                    ocr_out = reader.readtext(gray_up, detail=1, allowlist=self.character_set)

                    best_e_txt = ""
                    best_e_conf = 0.0
                    for _, e_txt, e_conf in ocr_out:
                        clean_e = "".join(ch for ch in e_txt.strip().upper() if ch.isalnum())
                        if len(clean_e) > len(best_e_txt) or (len(clean_e) == len(best_e_txt) and float(e_conf) > best_e_conf):
                            best_e_txt = clean_e
                            best_e_conf = float(e_conf)

                    # Se nenhum caractere legível foi detectado pelo detector textual CRAFT/EasyOCR, rejeita falso positivo
                    if len(best_e_txt) < 4:
                        return RecognitionResult(
                            text="",
                            confidence=0.0,
                            raw_characters=best_e_txt,
                            is_trained_weights=True,
                            model_used="hybrid_rejected_no_text",
                        )

                    # Se a CRNN gerou 7 caracteres e compartilha >= 3 caracteres com a leitura do EasyOCR,
                    # e o EasyOCR teve confiança moderada (< 0.80) ou tamanho != 7, prioriza o refinamento da CRNN
                    if len(decoded_text) == 7 and confidence >= 0.75:
                        shared = sum(1 for ch in set(decoded_text) if ch in best_e_txt)
                        if shared >= 3 and (best_e_conf < 0.80 or len(best_e_txt) != 7):
                            return RecognitionResult(
                                text=decoded_text,
                                confidence=round(max(confidence, best_e_conf), 4),
                                raw_characters=best_e_txt,
                                is_trained_weights=True,
                                model_used="crnn_ctc+easyocr",
                            )

                    # Caso contrário, utiliza a leitura direta do EasyOCR
                    return RecognitionResult(
                        text=best_e_txt,
                        confidence=round(best_e_conf, 4),
                        raw_characters=best_e_txt,
                        is_trained_weights=True,
                        model_used="easyocr",
                    )
                except Exception:
                    pass

        return RecognitionResult(
            text=decoded_text,
            confidence=round(confidence, 4),
            raw_characters=decoded_text,
            is_trained_weights=True,
            model_used="crnn_ctc",
        )


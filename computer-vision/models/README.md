# Modelos e Pesos — Módulo de Visão Computacional (ALPR)

Este documento descreve as especificações técnicas, arquitetura de redes neurais, alfabeto regulamentar e instruções de treinamento e integração dos modelos utilizados no pipeline ALPR.

---

## 1. Detector de Veículos (YOLOv8)

- **Arquivo:** `yolov8n.pt` (ou superior: `yolov8s.pt`, `yolov8m.pt`)
- **Origem dos pesos:** Modelos oficiais pré-treinados pela Ultralytics no dataset COCO. O download ocorre automaticamente na primeira execução através da biblioteca `ultralytics`.
- **Classes filtradas:**
  - `2`: `car` (automóveis de passeio)
  - `3`: `motorcycle` (motocicletas)
  - `5`: `bus` (ônibus)
  - `7`: `truck` (caminhões)
- **Função no pipeline:** Localiza a região do veículo (`VehicleDetection.bbox`) e recorta a ROI com padding configurável, restringindo o espaço de busca para a detecção de placas.

---

## 2. Detector Especializado de Placas (YOLO Customizado)

- **Caminho configurado:** `models/weights/plate_detector_yolo.pt`
- **Nota técnica de conformidade:** Um modelo YOLO genérico treinado em COCO **não** detecta placas de veículos. Para detectar placas em produção, utiliza-se uma rede YOLO fine-tuned em datasets de placas veiculares (como o *Brazilian License Plate Dataset* ou *UFPR-ALPR*).
- **Como obter ou treinar:**
  1. Coletar ou utilizar o dataset [UFPR-ALPR](https://web.inf.ufpr.br/vri/databases/ufpr-alpr/) ou [OpenALPR-BR](https://github.com/openalpr/openalpr).
  2. Treinar uma arquitetura YOLOv8 nano/small com anotações de classe única (`plate`):
     ```bash
     yolo detect train data=plates_dataset.yaml model=yolov8n.pt epochs=100 imgsz=640
     ```
  3. Exportar os melhores pesos (`best.pt`) e salvar em `computer-vision/models/weights/plate_detector_yolo.pt`.
- **Comportamento quando os pesos não estão presentes:**
  - A classe `PlateDetector` verifica via método `is_model_available` a existência do arquivo. Se ausente, o pipeline não gera detecções fictícias e permite testes unitários com injeção de bounding boxes e imagens sintéticas.

---

## 3. Reconhecedor Óptico de Caracteres (CRNN PyTorch)

- **Caminho configurado:** `models/weights/crnn_plate_recognition.pth`
- **Arquitetura da rede (`CRNNNet`):**
  1. **CNN (Feature Extractor):**
     - Camadas convolucionais VGG com BatchNorm e MaxPool não-quadrado para preservar a resolução horizontal dos caracteres:
     - Entrada: Tensor monocanal normalizado `[Batch, 1, H=32, W=128]`
     - Saída CNN: Mapa de características `[Batch, 512, 1, W_seq=31]`
  2. **RNN (Modelagem Sequencial):**
     - Squeeze na dimensão vertical e transposição para `[Seq_len=31, Batch, Features=512]`
     - Duas camadas de `nn.LSTM` bidirecional com `hidden_size=256` (saída 512 por timestep).
  3. **Camada Linear e Projeção:**
     - `nn.Linear(512, num_classes)`
     - `num_classes = len(alfabeto) + 1` (onde o índice `0` é estritamente o `CTC Blank Token`).

### 3.1. Alfabeto Oficial Suportado
O alfabeto para placas de trânsito no padrão brasileiro (Mercosul e Antigo) é composto por 36 caracteres alfanuméricos:
```text
0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ
```
- Total de classes: 37 (1 blank + 36 símbolos).

### 3.2. Procedimento de Inferência e Decodificação
1. **Pré-processamento da ROI da placa:** Conversão para escala de cinza, redimensionamento para `128x32`, equalização adaptativa CLAHE e normalização `[0, 1]` com padronização z-score `(x - 0.5) / 0.5`.
2. **Forward Pass:** A imagem é enviada ao dispositivo alvo (`mps` no Apple Silicon, `cuda` em GPU ou `cpu`).
3. **Decodificação CTC Greedy:**
   - Para cada passo temporal $t \in [1..31]$, extrai-se $\text{argmax}(\text{softmax}(\text{logits}))$.
   - Colapsam-se repetições consecutivas do mesmo caractere.
   - Descartam-se todos os tokens correspondentes ao índice `blank` (0).
   - A confiança média é calculada sobre a probabilidade dos caracteres emitidos.

### 3.3. Treinamento da CRNN
Para treinar os pesos `crnn_plate_recognition.pth`:
- Utilizar a loss `torch.nn.CTCLoss(blank=0, zero_infinity=True)`.
- Gerar imagens sintéticas de placas brasileiras com fontes oficiais (*FE-Schrift* e *Mandatory*) com data augmentation (ruído, iluminação, perspectiva).
- Salvar o `state_dict` do PyTorch no caminho indicado.

---

## 4. Validação Regulamentar de Placas Brasileiras

O módulo `PlateValidator` aplica expressões regulares sem substituição arbitrária de caracteres:
- **Padrão Mercosul:** `^[A-Z]{3}[0-9][A-Z][0-9]{2}$` (exemplo: `BRA2E19`)
- **Padrão Antigo (Cinza):** `^[A-Z]{3}[0-9]{4}$` (exemplo: `ABC1234`)
- Entradas que não correspondam exatamente a 7 caracteres alfanuméricos são registradas como inválidas, garantindo a integridade dos dados e prevenindo erros de bilhetagem.

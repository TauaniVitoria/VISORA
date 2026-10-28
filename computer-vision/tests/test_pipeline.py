"""
Testes de integração para o pipeline completo ALPR (ALPRPipeline).
Valida processamento ponta a ponta sobre vídeo de teste, telemetria,
geração de métricas e exportação de relatórios em formatos CSV e JSON.
"""

import json
from pathlib import Path
import cv2
import numpy as np
import pytest

from alpr.pipeline import ALPRPipeline


@pytest.fixture
def synthetic_test_video(tmp_path: Path) -> Path:
    """Gera um vídeo sintético de 5 quadros com resolução padrão."""
    video_path = tmp_path / "integration_test.mp4"
    width, height, fps = 640, 480, 15.0
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(video_path), fourcc, fps, (width, height))

    for i in range(5):
        frame = np.full((height, width, 3), fill_value=120, dtype=np.uint8)
        # Desenha retângulo simulando um veículo
        cv2.rectangle(frame, (100, 150), (450, 400), (40, 40, 40), -1)
        # Desenha placa retangular branca simulada
        cv2.rectangle(frame, (220, 320), (340, 360), (255, 255, 255), -1)
        cv2.putText(frame, "BRA2E19", (230, 350), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        writer.write(frame)

    writer.release()
    return video_path


def test_pipeline_end_to_end_execution(synthetic_test_video: Path, tmp_path: Path):
    """Executa o pipeline completo sobre o vídeo sintético e valida artefatos gerados."""
    config_path = Path("computer-vision/config/alpr_config.yaml")
    assert config_path.exists(), "Arquivo alpr_config.yaml deve existir para o teste."

    pipeline = ALPRPipeline(config_path=config_path)

    output_dir = tmp_path / "alpr_output"
    events, metrics = pipeline.process_video(
        video_path=synthetic_test_video,
        output_dir=output_dir,
        max_frames=5,
        save_video=True,
    )

    # 1. Validação das métricas
    assert metrics.total_frames_processed == 5
    assert metrics.processing_time_seconds > 0.0
    assert metrics.average_fps > 0.0
    assert metrics.video_path == str(synthetic_test_video.resolve())

    # 2. Validação da exportação do vídeo anotado
    annotated_video = output_dir / f"annotated_{synthetic_test_video.stem}.mp4"
    assert annotated_video.exists()
    assert annotated_video.stat().st_size > 0

    # 3. Validação do arquivo CSV
    csv_file = output_dir / f"passages_{synthetic_test_video.stem}.csv"
    assert csv_file.exists()
    csv_content = csv_file.read_text(encoding="utf-8")
    assert "track_id,vehicle_class,plate" in csv_content

    # 4. Validação do arquivo JSON
    json_file = output_dir / f"summary_{synthetic_test_video.stem}.json"
    assert json_file.exists()
    json_data = json.loads(json_file.read_text(encoding="utf-8"))
    assert "metrics" in json_data
    assert "events" in json_data
    assert json_data["metrics"]["total_frames_processed"] == 5


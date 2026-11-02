"""
Testes de Integração da Fase 5: ALPR + Câmeras + Backend.
Valida o gerenciamento de câmeras, ingestão de vídeo via pipeline de visão computacional,
conversão de passagens em movimentações de entrada e saída, cálculo tarifário e isolamento multi-tenant.
"""

from pathlib import Path
import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.models.entities import Estacionamento, Movimentacao, MovimentacaoStatus


@pytest.fixture
def synthetic_alpr_video(tmp_path: Path) -> Path:
    """Gera um vídeo sintético curto com representação gráfica de veículo e placa."""
    video_path = tmp_path / "test_gate_stream.mp4"
    width, height, fps = 640, 480, 10.0
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(video_path), fourcc, fps, (width, height))

    for _ in range(4):
        frame = np.full((height, width, 3), fill_value=120, dtype=np.uint8)
        # Bounding box simulando veículo
        cv2.rectangle(frame, (100, 150), (450, 400), (50, 50, 50), -1)
        # Bounding box simulando placa Mercosul
        cv2.rectangle(frame, (220, 320), (340, 360), (255, 255, 255), -1)
        cv2.putText(frame, "BRA2E19", (230, 350), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        writer.write(frame)

    writer.release()
    return video_path


def test_camera_crud_lifecycle(client: TestClient, tenant_a_token: str):
    """Testa o ciclo de vida completo de cadastro, listagem, atualização e remoção de câmeras."""
    headers = {"Authorization": f"Bearer {tenant_a_token}"}

    # 1. Cria câmera de entrada
    res_create = client.post(
        "/api/v1/cameras/",
        headers=headers,
        json={
            "identificador": "CAM-ENTRADA-01",
            "tipo": "entrada",
            "rtsp_url": "rtsp://192.168.1.100:554/live/ch0",
            "localizacao": "Cancela Principal Norte",
            "ativa": True,
        },
    )
    assert res_create.status_code == 201
    camera_data = res_create.json()
    assert camera_data["identificador"] == "CAM-ENTRADA-01"
    assert camera_data["tipo"] == "entrada"
    camera_id = camera_data["id"]

    # 2. Listagem
    res_list = client.get("/api/v1/cameras/", headers=headers)
    assert res_list.status_code == 200
    cameras = res_list.json()
    assert len(cameras) >= 1
    assert any(c["id"] == camera_id for c in cameras)

    # 3. Consulta individual
    res_get = client.get(f"/api/v1/cameras/{camera_id}", headers=headers)
    assert res_get.status_code == 200
    assert res_get.json()["identificador"] == "CAM-ENTRADA-01"

    # 4. Atualização
    res_update = client.put(
        f"/api/v1/cameras/{camera_id}",
        headers=headers,
        json={"localizacao": "Cancela Principal Norte - Pista 1", "ativa": True},
    )
    assert res_update.status_code == 200
    assert res_update.json()["localizacao"] == "Cancela Principal Norte - Pista 1"

    # 5. Remoção
    res_del = client.delete(f"/api/v1/cameras/{camera_id}", headers=headers)
    assert res_del.status_code == 204

    # 6. Verifica que não existe mais
    res_get_after = client.get(f"/api/v1/cameras/{camera_id}", headers=headers)
    assert res_get_after.status_code == 404


def test_camera_tenant_isolation(
    client: TestClient,
    tenant_a_token: str,
    tenant_b_token: str,
):
    """Garante que o Tenant B não pode consultar, alterar ou excluir câmeras do Tenant A."""
    headers_a = {"Authorization": f"Bearer {tenant_a_token}"}
    headers_b = {"Authorization": f"Bearer {tenant_b_token}"}

    # Tenant A cria uma câmera
    res_create = client.post(
        "/api/v1/cameras/",
        headers=headers_a,
        json={"identificador": "CAM-A-PRIVADA", "tipo": "ambos", "ativa": True},
    )
    assert res_create.status_code == 201
    camera_a_id = res_create.json()["id"]

    # Tenant B tenta consultar câmera do Tenant A -> 404
    res_get_b = client.get(f"/api/v1/cameras/{camera_a_id}", headers=headers_b)
    assert res_get_b.status_code == 404

    # Tenant B tenta excluir câmera do Tenant A -> 404
    res_del_b = client.delete(f"/api/v1/cameras/{camera_a_id}", headers=headers_b)
    assert res_del_b.status_code == 404


def test_alpr_simulate_detection_cycle(client: TestClient, tenant_a_token: str):
    """Testa a simulação de detecção ALPR em tempo real (entrada automática seguida de saída)."""
    headers = {"Authorization": f"Bearer {tenant_a_token}"}

    # 1. Primeira detecção: veículo entra
    res_entry = client.post(
        "/api/v1/alpr/simulate-detection",
        headers=headers,
        json={
            "placa": "RIO2A18",
            "tipo_evento": "auto",
            "ocr_confidence": 0.98,
            "det_confidence": 0.94,
        },
    )
    assert res_entry.status_code == 200
    entry_data = res_entry.json()
    assert entry_data["plate"] == "RIO2A18"
    assert entry_data["tipo_evento"] == "entrada"
    assert entry_data["status_movimentacao"] == "aberta"
    assert entry_data["movement_id"] is not None

    # 2. Segunda detecção da mesma placa com 'auto': detecta que já está dentro e processa a saída
    res_exit = client.post(
        "/api/v1/alpr/simulate-detection",
        headers=headers,
        json={
            "placa": "RIO2A18",
            "tipo_evento": "auto",
            "ocr_confidence": 0.97,
            "det_confidence": 0.92,
        },
    )
    assert res_exit.status_code == 200
    exit_data = res_exit.json()
    assert exit_data["plate"] == "RIO2A18"
    assert exit_data["tipo_evento"] == "saida"
    assert exit_data["status_movimentacao"] == "concluida"


def test_alpr_process_video_endpoint(
    client: TestClient,
    tenant_a_token: str,
    synthetic_alpr_video: Path,
):
    """Testa o processamento de arquivo de vídeo pelo pipeline ALPR integrado ao backend."""
    headers = {"Authorization": f"Bearer {tenant_a_token}"}

    res = client.post(
        "/api/v1/alpr/process-video",
        headers=headers,
        data={
            "video_path": str(synthetic_alpr_video),
            "sentido_default": "entrada",
            "max_frames": 4,
            "save_annotated_video": False,
        },
    )
    assert res.status_code == 200
    data = res.json()

    assert data["total_frames_processed"] == 4
    assert data["processing_time_seconds"] > 0
    assert data["average_fps"] > 0
    assert "passages" in data
    assert "movements_registered" in data


def test_alpr_upload_video_file(
    client: TestClient,
    tenant_a_token: str,
    synthetic_alpr_video: Path,
):
    """Testa o upload direto de arquivo de vídeo via multipart/form-data para ingestão ALPR."""
    headers = {"Authorization": f"Bearer {tenant_a_token}"}

    with open(synthetic_alpr_video, "rb") as f:
        files = {"video_file": ("camera_sample.mp4", f, "video/mp4")}
        data = {
            "sentido_default": "auto",
            "max_frames": 3,
        }
        res = client.post(
            "/api/v1/alpr/process-video",
            headers=headers,
            files=files,
            data=data,
        )

    assert res.status_code == 200
    result = res.json()
    assert result["total_frames_processed"] == 3
    assert result["processing_time_seconds"] > 0


def test_alpr_pipeline_singleton_reuse_and_security(
    client: TestClient,
    tenant_a_token: str,
):
    """Garante reuso singleton do ALPRPipeline em memória e proteção contra path traversal / extensões inválidas."""
    from app.services.alpr_service import ALPRService

    p1 = ALPRService.get_pipeline()
    p2 = ALPRService.get_pipeline()
    assert p1 is p2

    headers = {"Authorization": f"Bearer {tenant_a_token}"}

    # Rejeita path traversal em video_path
    res_traversal = client.post(
        "/api/v1/alpr/process-video",
        headers=headers,
        data={"video_path": "../../etc/passwd"},
    )
    assert res_traversal.status_code == 400

    # Rejeita extensão inválida no upload
    files = {"video_file": ("malicious.exe", b"not-a-video", "application/octet-stream")}
    res_ext = client.post(
        "/api/v1/alpr/process-video",
        headers=headers,
        files=files,
    )
    assert res_ext.status_code == 400



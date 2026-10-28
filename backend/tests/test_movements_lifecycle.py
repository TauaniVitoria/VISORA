"""
Testes de ciclo de vida de permanência, bilhetagem automatizada, tarifação e auditoria.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from fastapi.testclient import TestClient


def test_entry_exit_lifecycle_with_tariff_calculation(client: TestClient, tenant_a_token: str):
    """
    Valida fluxo completo de entrada e saída com cálculo tarifário e tolerância:
    - Entrada de veículo avulso
    - Prevenção de duplicidade de permanência aberta
    - Saída com permanência de 90 minutos (Primeira hora R$ 15 + adicional R$ 5 = R$ 20.00)
    """
    headers = {"Authorization": f"Bearer {tenant_a_token}"}

    # Configura tarifa explícita: 1ª hora R$ 15, adicional R$ 5, tolerância 15 min
    tariff_payload = {
        "descricao": "Tarifa Comercial",
        "valor_primeira_hora": "15.00",
        "valor_hora_adicional": "5.00",
        "valor_diaria": "60.00",
        "tolerancia_minutos": 15,
    }
    client.post("/api/v1/tariffs-plans/tariffs", json=tariff_payload, headers=headers)

    t0 = datetime.now(timezone.utc)

    # 1. Entrada do veículo KGT9082
    entry_payload = {
        "placa": "KGT9082",
        "timestamp": t0.isoformat(),
    }
    resp_entry = client.post("/api/v1/movements/entry", json=entry_payload, headers=headers)
    assert resp_entry.status_code == 201
    entry_data = resp_entry.json()
    assert entry_data["status"] == "aberta"
    assert entry_data["placa"] == "KGT9082"

    # 2. Regra: Tentar registrar nova entrada enquanto aberta DEVE ser rejeitado com 400
    resp_dup_entry = client.post("/api/v1/movements/entry", json=entry_payload, headers=headers)
    assert resp_dup_entry.status_code == 400
    assert "já possui permanência aberta" in resp_dup_entry.json()["detail"]

    # 3. Saída após 90 minutos
    t_exit = t0 + timedelta(minutes=90)
    exit_payload = {
        "placa": "KGT9082",
        "timestamp": t_exit.isoformat(),
    }
    resp_exit = client.post("/api/v1/movements/exit", json=exit_payload, headers=headers)
    assert resp_exit.status_code == 200
    exit_data = resp_exit.json()
    assert exit_data["status"] == "concluida"
    assert exit_data["permanencia_minutos"] == 90

    # 4. Verifica cobrança gerada: R$ 15.00 (1ª hora) + R$ 5.00 (30 min adicionais) = R$ 20.00
    assert exit_data["cobranca"] is not None
    assert Decimal(exit_data["cobranca"]["valor_liquido"]) == Decimal("20.00")
    assert exit_data["cobranca"]["status"] == "pendente"


def test_tolerance_free_exit(client: TestClient, tenant_a_token: str):
    """Valida isenção de cobrança quando a permanência é inferior à tolerância (10 min < 15 min)."""
    headers = {"Authorization": f"Bearer {tenant_a_token}"}
    t0 = datetime.now(timezone.utc)

    # Entrada
    client.post(
        "/api/v1/movements/entry",
        json={"placa": "RAPIDO1", "timestamp": t0.isoformat()},
        headers=headers,
    )

    # Saída após 10 minutos
    t_exit = t0 + timedelta(minutes=10)
    resp_exit = client.post(
        "/api/v1/movements/exit",
        json={"placa": "RAPIDO1", "timestamp": t_exit.isoformat()},
        headers=headers,
    )
    assert resp_exit.status_code == 200
    cobranca = resp_exit.json()["cobranca"]
    assert Decimal(cobranca["valor_liquido"]) == Decimal("0.00")
    assert cobranca["status"] == "pago"


def test_exit_without_entry_records_inconsistency(client: TestClient, tenant_a_token: str):
    """Valida registro de inconsistência quando um veículo sai sem ter registrado entrada."""
    headers = {"Authorization": f"Bearer {tenant_a_token}"}
    resp = client.post(
        "/api/v1/movements/exit",
        json={"placa": "FANTASMA1"},
        headers=headers,
    )
    assert resp.status_code == 404
    assert "Inconsistência registrada" in resp.json()["detail"]


def test_manual_correction_and_audit(client: TestClient, tenant_a_token: str):
    """Valida alteração manual de placa/status e conferência do registro de auditoria."""
    headers = {"Authorization": f"Bearer {tenant_a_token}"}

    # Entrada com placa com erro de leitura (ex: OCR leu BRA2E18 em vez de BRA2E19)
    resp_entry = client.post("/api/v1/movements/entry", json={"placa": "BRA2E18"}, headers=headers)
    assert resp_entry.status_code == 201
    mov_id = resp_entry.json()["id"]

    # Correção manual com justificativa
    correction_payload = {
        "placa": "BRA2E19",
        "observacao": "Operador corrigiu dígito final da placa após conferência visual.",
    }
    resp_corr = client.patch(
        f"/api/v1/movements/{mov_id}/correction",
        json=correction_payload,
        headers=headers,
    )
    assert resp_corr.status_code == 200
    assert resp_corr.json()["placa"] == "BRA2E19"

    # Valida presença no log de auditoria
    resp_audit = client.get("/api/v1/audit/", headers=headers)
    assert resp_audit.status_code == 200
    logs = resp_audit.json()
    assert len(logs) >= 1
    assert logs[0]["acao"] == "CORRECAO_MANUAL_MOVIMENTACAO"
    assert logs[0]["dados_anteriores"]["placa"] == "BRA2E18"
    assert logs[0]["dados_novos"]["placa"] == "BRA2E19"


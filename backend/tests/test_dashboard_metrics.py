"""
Testes de métricas e indicadores do Dashboard Administrativo.
"""

from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient


def test_dashboard_metrics(client: TestClient, tenant_a_token: str):
    """Valida a consolidação dos dados agregados no dashboard do estacionamento."""
    headers = {"Authorization": f"Bearer {tenant_a_token}"}

    # 1. Realiza entrada de 2 veículos (CARRO01 entrou há 30 min, CARRO02 agora) e saída de 1
    t_entry_1 = datetime.now(timezone.utc) - timedelta(minutes=30)
    t_exit_1 = datetime.now(timezone.utc)

    client.post("/api/v1/movements/entry", json={"placa": "CARRO01", "timestamp": t_entry_1.isoformat()}, headers=headers)
    client.post("/api/v1/movements/entry", json={"placa": "CARRO02"}, headers=headers)
    resp_exit = client.post("/api/v1/movements/exit", json={"placa": "CARRO01", "timestamp": t_exit_1.isoformat()}, headers=headers)

    # 2. Paga a cobrança do CARRO01
    cobranca_id = resp_exit.json()["cobranca"]["id"]
    client.post(
        "/api/v1/billing/payments",
        json={"cobranca_id": cobranca_id, "valor_pago": "15.00", "metodo": "dinheiro"},
        headers=headers,
    )

    # 3. Consulta métricas do dashboard
    resp = client.get("/api/v1/dashboard/metrics", headers=headers)
    assert resp.status_code == 200
    metrics = resp.json()

    assert metrics["veiculos_estacionados_agora"] == 1  # Apenas CARRO02 continua estacionado
    assert metrics["entradas_hoje"] >= 2
    assert metrics["saidas_hoje"] >= 1
    assert float(metrics["receita_total_registrada"]) >= 15.0
    assert "movimentacoes_recentes" in metrics
    assert isinstance(metrics["movimentacoes_recentes"], list)
    assert len(metrics["movimentacoes_recentes"]) >= 2


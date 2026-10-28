"""
Testes para módulos de cobrança e registro manual de pagamentos.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from fastapi.testclient import TestClient


def test_payment_settlement(client: TestClient, tenant_a_token: str):
    """Valida registro manual de pagamento e liquidação da cobrança."""
    headers = {"Authorization": f"Bearer {tenant_a_token}"}

    # 1. Gera uma movimentação com permanência de 30 minutos (acima da tolerância de 15m)
    t_entry = datetime.now(timezone.utc) - timedelta(minutes=30)
    t_exit = datetime.now(timezone.utc)

    client.post("/api/v1/movements/entry", json={"placa": "PAGAR01", "timestamp": t_entry.isoformat()}, headers=headers)
    resp_exit = client.post("/api/v1/movements/exit", json={"placa": "PAGAR01", "timestamp": t_exit.isoformat()}, headers=headers)
    assert resp_exit.status_code == 200
    cobranca_id = resp_exit.json()["cobranca"]["id"]
    valor_liquido = resp_exit.json()["cobranca"]["valor_liquido"]
    assert Decimal(valor_liquido) > Decimal("0.00")
    assert resp_exit.json()["cobranca"]["status"] == "pendente"

    # 2. Registra o pagamento integral via PIX
    payment_payload = {
        "cobranca_id": cobranca_id,
        "valor_pago": valor_liquido,
        "metodo": "pix",
        "comprovante_transacao": "PIX-123456789",
    }
    resp_pay = client.post("/api/v1/billing/payments", json=payment_payload, headers=headers)
    assert resp_pay.status_code == 201
    assert resp_pay.json()["metodo"] == "pix"

    # 3. Verifica se a cobrança foi liquidada (status pago)
    resp_charges = client.get("/api/v1/billing/charges?status_filter=pago", headers=headers)
    assert resp_charges.status_code == 200
    charges = resp_charges.json()
    assert any(c["id"] == cobranca_id for c in charges)


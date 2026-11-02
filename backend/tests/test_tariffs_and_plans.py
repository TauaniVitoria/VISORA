"""
Testes adicionais de regras de negócio: validação de vínculo de veículo com cliente na assinatura.
"""

import pytest
from datetime import date
from fastapi.testclient import TestClient

def test_subscription_requires_vehicle_owned_by_customer(client: TestClient, tenant_a_token: str):
    headers = {"Authorization": f"Bearer {tenant_a_token}"}

    # Cria cliente 1 com veículo 1
    c1 = client.post("/api/v1/customers/", headers=headers, json={
        "nome": "Cliente Alpha",
        "documento": "11100022233",
        "tipo_documento": "CPF",
        "telefone": "(11) 98888-0001",
        "plano_tipo": "mensal",
        "veiculos_iniciais": [{"placa": "ALP1A01", "tipo": "carro"}],
    }).json()

    # Cria cliente 2 com veículo 2
    c2 = client.post("/api/v1/customers/", headers=headers, json={
        "nome": "Cliente Beta",
        "documento": "22200033344",
        "tipo_documento": "CPF",
        "telefone": "(11) 98888-0002",
        "plano_tipo": "anual",
        "veiculos_iniciais": [{"placa": "BET2B02", "tipo": "carro"}],
    }).json()

    # Cria plano
    plan = client.post("/api/v1/tariffs-plans/plans", headers=headers, json={
        "nome": "Plano Corporativo",
        "tipo_recorrencia": "mensal",
        "valor_base": "200.00",
        "limite_veiculos": 1,
    }).json()

    # Tenta criar assinatura para Cliente 1 usando veículo pertencente ao Cliente 2 -> deve retornar 400
    v2_id = c2["veiculos"][0]["id"]
    resp = client.post("/api/v1/tariffs-plans/subscriptions", headers=headers, json={
        "cliente_id": c1["id"],
        "plano_id": plan["id"],
        "veiculos_ids": [v2_id],
        "data_inicio": str(date.today()),
    })
    assert resp.status_code == 400
    assert "não pertence ao cliente" in resp.json()["detail"].lower()

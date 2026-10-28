"""
Testes unitários e de regras de negócio para Clientes e Veículos.
"""

from fastapi.testclient import TestClient


def test_customer_creation_requires_initial_vehicle(client: TestClient, tenant_a_token: str):
    """Valida a regra de negócio: cadastro inicial deve conter pelo menos 1 veículo."""
    headers = {"Authorization": f"Bearer {tenant_a_token}"}
    payload_invalid = {
        "nome": "Carlos Cliente",
        "documento": "11122233344",
        "tipo_documento": "CPF",
        "veiculos_iniciais": [],  # Lista vazia de veículos -> Deve falhar na validação
    }
    response = client.post("/api/v1/customers/", json=payload_invalid, headers=headers)
    assert response.status_code == 422


def test_prevent_duplicate_plates_in_same_tenant(client: TestClient, tenant_a_token: str):
    """Valida que não é permitido cadastrar duas vezes a mesma placa no mesmo estacionamento."""
    headers = {"Authorization": f"Bearer {tenant_a_token}"}

    payload_1 = {
        "nome": "Cliente Um",
        "documento": "22233344455",
        "tipo_documento": "CPF",
        "veiculos_iniciais": [{"placa": "XYZ9F88", "tipo": "carro"}],
    }
    res_1 = client.post("/api/v1/customers/", json=payload_1, headers=headers)
    assert res_1.status_code == 201

    payload_2 = {
        "nome": "Cliente Dois",
        "documento": "66677788899",
        "tipo_documento": "CPF",
        "veiculos_iniciais": [{"placa": "XYZ-9F88", "tipo": "carro"}],  # Mesma placa com hífen
    }
    res_2 = client.post("/api/v1/customers/", json=payload_2, headers=headers)
    assert res_2.status_code == 400
    assert "já está cadastrada" in res_2.json()["detail"]


def test_add_vehicle_to_existing_customer(client: TestClient, tenant_a_token: str):
    """Valida adição de múltiplos veículos a um cliente existente."""
    headers = {"Authorization": f"Bearer {tenant_a_token}"}
    payload = {
        "nome": "Frota Express",
        "documento": "12312312000199",
        "tipo_documento": "CNPJ",
        "veiculos_iniciais": [{"placa": "ABC1D23", "tipo": "carro"}],
    }
    res = client.post("/api/v1/customers/", json=payload, headers=headers)
    assert res.status_code == 201
    cliente_id = res.json()["id"]

    # Adicionar 2º veículo
    veh_payload = {"placa": "ABC2E34", "tipo": "moto"}
    veh_res = client.post(f"/api/v1/customers/{cliente_id}/vehicles", json=veh_payload, headers=headers)
    assert veh_res.status_code == 201
    assert veh_res.json()["placa"] == "ABC2E34"


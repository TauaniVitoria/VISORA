"""
Testes de isolamento estrito de dados entre tenants (Multi-Tenancy).
Garante que um estacionamento jamais acesse ou interfira nos dados de outro.
"""

from fastapi.testclient import TestClient


def test_customer_and_vehicle_tenant_isolation(
    client: TestClient,
    tenant_a_token: str,
    tenant_b_token: str,
):
    """
    Valida que clientes e veículos de um tenant não aparecem em outro,
    e que a mesma placa veicular pode existir em dois estacionamentos distintos simultaneamente.
    """
    headers_a = {"Authorization": f"Bearer {tenant_a_token}"}
    headers_b = {"Authorization": f"Bearer {tenant_b_token}"}

    # 1. Tenant A cadastra cliente João com veículo BRA2E19
    payload_a = {
        "nome": "João da Silva",
        "documento": "12345678901",
        "tipo_documento": "CPF",
        "email": "joao@email.com",
        "veiculos_iniciais": [
            {"placa": "BRA2E19", "marca": "Toyota", "modelo": "Corolla", "cor": "Preto", "tipo": "carro"}
        ],
    }
    resp_create_a = client.post("/api/v1/customers/", json=payload_a, headers=headers_a)
    assert resp_create_a.status_code == 201
    customer_a_id = resp_create_a.json()["id"]

    # 2. Tenant B cadastra cliente Maria também com veículo BRA2E19
    # Deve ser PERMITIDO, pois pertencem a estacionamentos distintos!
    payload_b = {
        "nome": "Maria Souza",
        "documento": "98765432100",
        "tipo_documento": "CPF",
        "email": "maria@email.com",
        "veiculos_iniciais": [
            {"placa": "BRA2E19", "marca": "Honda", "modelo": "Civic", "cor": "Branco", "tipo": "carro"}
        ],
    }
    resp_create_b = client.post("/api/v1/customers/", json=payload_b, headers=headers_b)
    assert resp_create_b.status_code == 201

    # 3. Tenant B lista clientes: DEVE conter apenas Maria, NUNCA João
    resp_list_b = client.get("/api/v1/customers/", headers=headers_b)
    assert resp_list_b.status_code == 200
    b_customers = resp_list_b.json()
    assert len(b_customers) == 1
    assert b_customers[0]["nome"] == "Maria Souza"

    # 4. Tenant B tenta acessar diretamente o ID do cliente do Tenant A -> 404 Not Found
    resp_get_cross_tenant = client.get(f"/api/v1/customers/{customer_a_id}", headers=headers_b)
    assert resp_get_cross_tenant.status_code == 404


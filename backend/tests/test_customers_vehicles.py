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
        "telefone": "(11) 98765-4321",
        "plano_tipo": "diario",
        "veiculos_iniciais": [],  # Lista vazia de veículos -> Deve falhar na validação
    }
    response = client.post("/api/v1/customers/", json=payload_invalid, headers=headers)
    assert response.status_code == 422


def test_customer_creation_requires_mandatory_phone_and_plan(client: TestClient, tenant_a_token: str):
    """Valida que telefone e plano são campos obrigatórios."""
    headers = {"Authorization": f"Bearer {tenant_a_token}"}

    # Sem plano
    res_no_plan = client.post("/api/v1/customers/", json={
        "nome": "Sem Plano",
        "documento": "12345678909",
        "tipo_documento": "CPF",
        "telefone": "(11) 98765-0000",
        "veiculos_iniciais": [{"placa": "NOP1A00", "tipo": "carro"}],
    }, headers=headers)
    assert res_no_plan.status_code == 422

    # Plano inválido
    res_bad_plan = client.post("/api/v1/customers/", json={
        "nome": "Plano Invalido",
        "documento": "12345678909",
        "tipo_documento": "CPF",
        "telefone": "(11) 98765-0000",
        "plano_tipo": "quinzenal",  # Invalido: permitido apenas diario ou mensal
        "veiculos_iniciais": [{"placa": "NOP1A00", "tipo": "carro"}],
    }, headers=headers)
    assert res_bad_plan.status_code == 422

    # Plano anual e mensal foram descontinuados e não são mais aceitos
    res_anual = client.post("/api/v1/customers/", json={
        "nome": "Plano Anual",
        "documento": "12345678909",
        "tipo_documento": "CPF",
        "telefone": "(11) 98765-0000",
        "plano_tipo": "anual",
        "veiculos_iniciais": [{"placa": "NOP1A00", "tipo": "carro"}],
    }, headers=headers)
    assert res_anual.status_code == 422

    res_mensal = client.post("/api/v1/customers/", json={
        "nome": "Plano Mensal",
        "documento": "12345678909",
        "tipo_documento": "CPF",
        "telefone": "(11) 98765-0000",
        "plano_tipo": "mensal",
        "veiculos_iniciais": [{"placa": "NOP1A00", "tipo": "carro"}],
    }, headers=headers)
    assert res_mensal.status_code == 422

    # Recorrência anual e mensal também não são aceitas na criação de planos
    res_plan_anual = client.post("/api/v1/tariffs-plans/plans", json={
        "nome": "Plano Anual",
        "tipo_recorrencia": "anual",
        "valor_base": "1000.00",
        "limite_veiculos": 1,
    }, headers=headers)
    assert res_plan_anual.status_code == 422

    res_plan_mensal = client.post("/api/v1/tariffs-plans/plans", json={
        "nome": "Plano Mensal",
        "tipo_recorrencia": "mensal",
        "valor_base": "250.00",
        "limite_veiculos": 1,
    }, headers=headers)
    assert res_plan_mensal.status_code == 422

    # Sem telefone
    res_no_phone = client.post("/api/v1/customers/", json={
        "nome": "Sem Telefone",
        "documento": "12345678909",
        "tipo_documento": "CPF",
        "plano_tipo": "diario",
        "veiculos_iniciais": [{"placa": "NOP1A00", "tipo": "carro"}],
    }, headers=headers)
    assert res_no_phone.status_code == 422


def test_prevent_duplicate_plates_in_same_tenant(client: TestClient, tenant_a_token: str):
    """Valida que não é permitido cadastrar duas vezes a mesma placa no mesmo estacionamento."""
    headers = {"Authorization": f"Bearer {tenant_a_token}"}

    payload_1 = {
        "nome": "Cliente Um",
        "documento": "22233344455",
        "tipo_documento": "CPF",
        "telefone": "(11) 98765-1111",
        "plano_tipo": "diario",
        "veiculos_iniciais": [{"placa": "XYZ9F88", "tipo": "carro"}],
    }
    res_1 = client.post("/api/v1/customers/", json=payload_1, headers=headers)
    assert res_1.status_code == 201
    assert "codigo" in res_1.json()
    assert res_1.json()["codigo"].startswith("CLI-")
    assert res_1.json()["plano_tipo"] == "diario"

    payload_2 = {
        "nome": "Cliente Dois",
        "documento": "66677788899",
        "tipo_documento": "CPF",
        "telefone": "(11) 98765-2222",
        "plano_tipo": "diario",
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
        "telefone": "(11) 3214-0000",
        "plano_tipo": "diario",
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

    # Consultar movimentações do cliente (deve retornar lista, inicialmente vazia)
    mov_res = client.get(f"/api/v1/customers/{cliente_id}/movements", headers=headers)
    assert mov_res.status_code == 200
    assert isinstance(mov_res.json(), list)


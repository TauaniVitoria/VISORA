"""
Script para popular o banco de dados com dados de demonstração (10 clientes e 10 veículos).

Uso (a partir da pasta backend/):
    python scripts/seed_demo_data.py
"""

from datetime import datetime, timezone
from decimal import Decimal
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import SessionLocal  # noqa: E402
from app.models.entities import Cliente, Estacionamento, Tarifa, Usuario, Veiculo  # noqa: E402


def seed_data() -> None:
    with SessionLocal() as db:
        estacionamento = db.query(Estacionamento).first()
        if not estacionamento:
            estacionamento = Estacionamento(
                nome_fantasia="Estacionamento Central Park",
                razao_social="Central Park Estacionamentos e Servicos Ltda",
                cnpj="12.345.678/0001-90",
                email_contato="contato@centralpark.com.br",
                telefone="(11) 3214-5500",
                status="ativo",
            )
            db.add(estacionamento)
            db.flush()

        print(f"Estacionamento: {estacionamento.nome_fantasia} ({estacionamento.id})")

        # Vincular admin se não possuir estacionamento
        admin_user = db.query(Usuario).filter_by(email="admin@parkalpr.com").first()
        if admin_user and not admin_user.estacionamento_id:
            admin_user.estacionamento_id = estacionamento.id
            db.add(admin_user)

        # Tarifa vigente default
        tarifa = db.query(Tarifa).filter_by(estacionamento_id=estacionamento.id).first()
        if not tarifa:
            tarifa = Tarifa(
                estacionamento_id=estacionamento.id,
                descricao="Tarifa Padrao",
                valor_primeira_hora=Decimal("15.00"),
                valor_hora_adicional=Decimal("5.00"),
                valor_diaria=Decimal("60.00"),
                tolerancia_minutos=15,
                vigente_desde=datetime.now(timezone.utc),
            )
            db.add(tarifa)

        dados = [
            {
                "nome": "Carlos Eduardo da Silva",
                "documento": "123.456.789-01",
                "tipo_doc": "cpf",
                "email": "carlos.silva@email.com",
                "telefone": "(11) 98765-4321",
                "placa": "BRA2E19",
                "marca": "Toyota",
                "modelo": "Corolla XEi",
                "cor": "Prata",
                "tipo": "carro",
            },
            {
                "nome": "Mariana Ferreira Santos",
                "documento": "234.567.890-12",
                "tipo_doc": "cpf",
                "email": "mariana.santos@email.com",
                "telefone": "(11) 97654-3210",
                "placa": "ABC1234",
                "marca": "Honda",
                "modelo": "Civic Touring",
                "cor": "Preto",
                "tipo": "carro",
            },
            {
                "nome": "Roberto Gonçalves Dias",
                "documento": "345.678.901-23",
                "tipo_doc": "cpf",
                "email": "roberto.dias@email.com",
                "telefone": "(11) 96543-2109",
                "placa": "RIO2A18",
                "marca": "Jeep",
                "modelo": "Compass Longitude",
                "cor": "Branco",
                "tipo": "carro",
            },
            {
                "nome": "Fernanda Lima de Oliveira",
                "documento": "456.789.012-34",
                "tipo_doc": "cpf",
                "email": "fernanda.oliveira@email.com",
                "telefone": "(11) 95432-1098",
                "placa": "KGT9082",
                "marca": "Volkswagen",
                "modelo": "Golf Highline",
                "cor": "Cinza",
                "tipo": "carro",
            },
            {
                "nome": "Lucas Gabriel Costa",
                "documento": "567.890.123-45",
                "tipo_doc": "cpf",
                "email": "lucas.costa@email.com",
                "telefone": "(11) 94321-0987",
                "placa": "XYZ9F88",
                "marca": "Hyundai",
                "modelo": "HB20 Evolution",
                "cor": "Vermelho",
                "tipo": "carro",
            },
            {
                "nome": "Beatriz Pereira Martins",
                "documento": "678.901.234-56",
                "tipo_doc": "cpf",
                "email": "beatriz.martins@email.com",
                "telefone": "(11) 93210-9876",
                "placa": "SP1234",
                "marca": "Chevrolet",
                "modelo": "Onix Premier",
                "cor": "Prata",
                "tipo": "carro",
            },
            {
                "nome": "Alexandre Carvalho Souza",
                "documento": "789.012.345-67",
                "tipo_doc": "cpf",
                "email": "alexandre.souza@email.com",
                "telefone": "(11) 92109-8765",
                "placa": "BRA3A20",
                "marca": "Fiat",
                "modelo": "Pulse Audace",
                "cor": "Azul",
                "tipo": "carro",
            },
            {
                "nome": "Juliana Mendes Castro",
                "documento": "890.123.456-78",
                "tipo_doc": "cpf",
                "email": "juliana.castro@email.com",
                "telefone": "(11) 91098-7654",
                "placa": "JKG4512",
                "marca": "Renault",
                "modelo": "Duster Iconic",
                "cor": "Verde",
                "tipo": "carro",
            },
            {
                "nome": "Thiago Alencar Moreira",
                "documento": "901.234.567-89",
                "tipo_doc": "cpf",
                "email": "thiago.moreira@email.com",
                "telefone": "(11) 90987-6543",
                "placa": "MER1B23",
                "marca": "Nissan",
                "modelo": "Kicks Exclusive",
                "cor": "Cinza Grafite",
                "tipo": "carro",
            },
            {
                "nome": "Camila Ribeiro Duarte",
                "documento": "012.345.678-90",
                "tipo_doc": "cpf",
                "email": "camila.duarte@email.com",
                "telefone": "(11) 99876-5432",
                "placa": "DFG7890",
                "marca": "BMW",
                "modelo": "320i M Sport",
                "cor": "Preto",
                "tipo": "carro",
            },
        ]

        novos_clientes = 0
        novos_veiculos = 0

        for item in dados:
            cliente = db.query(Cliente).filter_by(
                estacionamento_id=estacionamento.id,
                documento=item["documento"]
            ).first()

            if not cliente:
                cliente = Cliente(
                    estacionamento_id=estacionamento.id,
                    nome=item["nome"],
                    documento=item["documento"],
                    tipo_documento=item["tipo_doc"],
                    email=item["email"],
                    telefone=item["telefone"],
                )
                db.add(cliente)
                db.flush()
                novos_clientes += 1

            veiculo = db.query(Veiculo).filter_by(
                estacionamento_id=estacionamento.id,
                placa=item["placa"]
            ).first()

            if not veiculo:
                veiculo = Veiculo(
                    estacionamento_id=estacionamento.id,
                    cliente_id=cliente.id,
                    placa=item["placa"],
                    marca=item["marca"],
                    modelo=item["modelo"],
                    cor=item["cor"],
                    tipo=item["tipo"],
                    ativo=True,
                )
                db.add(veiculo)
                novos_veiculos += 1

        db.commit()
        print(f"Carga concluída: {novos_clientes} novos clientes e {novos_veiculos} novos veículos.")


if __name__ == "__main__":
    seed_data()


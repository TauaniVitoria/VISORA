"""
Script para popular o banco de dados com dados de demonstração:
- Clientes com códigos sequenciais CLI-0001 a CLI-0020
- Planos diversificados (diário e mensal)
- Múltiplos veículos por cliente (carros, motos, caminhões, ônibus)
- Movimentações reais (entradas, saídas, permanências, cobranças e veículos atualmente estacionados)

Uso (a partir da raiz do projeto):
    python backend/scripts/seed_demo_data.py
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import SessionLocal  # noqa: E402
from app.models.entities import (  # noqa: E402
    Camera,
    CameraTipo,
    Cliente,
    Cobranca,
    CobrancaStatus,
    Estacionamento,
    Movimentacao,
    MovimentacaoStatus,
    Tarifa,
    TipoCobranca,
    Usuario,
    Veiculo,
)


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

        # Câmeras de entrada e saída
        cam_in = db.query(Camera).filter_by(estacionamento_id=estacionamento.id, identificador="CAM-ENTRADA-01").first()
        if not cam_in:
            cam_in = Camera(
                estacionamento_id=estacionamento.id,
                identificador="CAM-ENTRADA-01",
                tipo=CameraTipo.ENTRADA.value,
                localizacao="Portão Principal - Entrada",
                ativa=True,
            )
            db.add(cam_in)
            db.flush()

        cam_out = db.query(Camera).filter_by(estacionamento_id=estacionamento.id, identificador="CAM-SAIDA-01").first()
        if not cam_out:
            cam_out = Camera(
                estacionamento_id=estacionamento.id,
                identificador="CAM-SAIDA-01",
                tipo=CameraTipo.SAIDA.value,
                localizacao="Portão Principal - Saída",
                ativa=True,
            )
            db.add(cam_out)
            db.flush()

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

        clientes_data = [
            # 1 a 10 (Iniciais)
            {
                "codigo": "CLI-0001",
                "nome": "Carlos Eduardo da Silva",
                "documento": "123.456.789-01",
                "tipo_doc": "CPF",
                "email": "carlos.silva@email.com",
                "telefone": "(11) 98765-4321",
                "plano_tipo": "mensal",
                "veiculos": [
                    {"placa": "BRA2E19", "marca": "Toyota", "modelo": "Corolla XEi", "cor": "Prata", "tipo": "carro"},
                    {"placa": "SPM1A90", "marca": "Honda", "modelo": "PCX 150", "cor": "Cinza", "tipo": "moto"},
                ],
            },
            {
                "codigo": "CLI-0002",
                "nome": "Mariana Ferreira Santos",
                "documento": "234.567.890-12",
                "tipo_doc": "CPF",
                "email": "mariana.santos@email.com",
                "telefone": "(11) 97654-3210",
                "plano_tipo": "mensal",
                "veiculos": [
                    {"placa": "ABC1234", "marca": "Honda", "modelo": "Civic Touring", "cor": "Preto", "tipo": "carro"},
                ],
            },
            {
                "codigo": "CLI-0003",
                "nome": "Roberto Gonçalves Dias",
                "documento": "345.678.901-23",
                "tipo_doc": "CPF",
                "email": "roberto.dias@email.com",
                "telefone": "(11) 96543-2109",
                "plano_tipo": "diario",
                "veiculos": [
                    {"placa": "RIO2A18", "marca": "Jeep", "modelo": "Compass Longitude", "cor": "Branco", "tipo": "carro"},
                ],
            },
            {
                "codigo": "CLI-0004",
                "nome": "Fernanda Lima de Oliveira",
                "documento": "456.789.012-34",
                "tipo_doc": "CPF",
                "email": "fernanda.oliveira@email.com",
                "telefone": "(11) 95432-1098",
                "plano_tipo": "mensal",
                "veiculos": [
                    {"placa": "KGT9082", "marca": "Volkswagen", "modelo": "Golf Highline", "cor": "Cinza", "tipo": "carro"},
                    {"placa": "FER4E56", "marca": "Fiat", "modelo": "500 Cult", "cor": "Vermelho", "tipo": "carro"},
                ],
            },
            {
                "codigo": "CLI-0005",
                "nome": "Lucas Gabriel Costa",
                "documento": "567.890.123-45",
                "tipo_doc": "CPF",
                "email": "lucas.costa@email.com",
                "telefone": "(11) 94321-0987",
                "plano_tipo": "diario",
                "veiculos": [
                    {"placa": "XYZ9F88", "marca": "Hyundai", "modelo": "HB20 Evolution", "cor": "Vermelho", "tipo": "carro"},
                ],
            },
            {
                "codigo": "CLI-0006",
                "nome": "Beatriz Pereira Martins",
                "documento": "678.901.234-56",
                "tipo_doc": "CPF",
                "email": "beatriz.martins@email.com",
                "telefone": "(11) 93210-9876",
                "plano_tipo": "mensal",
                "veiculos": [
                    {"placa": "SPF1234", "marca": "Chevrolet", "modelo": "Onix Premier", "cor": "Prata", "tipo": "carro"},
                ],
            },
            {
                "codigo": "CLI-0007",
                "nome": "Alexandre Carvalho Souza",
                "documento": "789.012.345-67",
                "tipo_doc": "CPF",
                "email": "alexandre.souza@email.com",
                "telefone": "(11) 92109-8765",
                "plano_tipo": "mensal",
                "veiculos": [
                    {"placa": "BRA3A20", "marca": "Fiat", "modelo": "Pulse Audace", "cor": "Azul", "tipo": "carro"},
                ],
            },
            {
                "codigo": "CLI-0008",
                "nome": "Juliana Mendes Castro",
                "documento": "890.123.456-78",
                "tipo_doc": "CPF",
                "email": "juliana.castro@email.com",
                "telefone": "(11) 91098-7654",
                "plano_tipo": "mensal",
                "veiculos": [
                    {"placa": "JKG4512", "marca": "Renault", "modelo": "Duster Iconic", "cor": "Verde", "tipo": "carro"},
                    {"placa": "JUL8A90", "marca": "Jeep", "modelo": "Renegade Trailhawk", "cor": "Verde Militar", "tipo": "carro"},
                ],
            },
            {
                "codigo": "CLI-0009",
                "nome": "Thiago Alencar Moreira",
                "documento": "901.234.567-89",
                "tipo_doc": "CPF",
                "email": "thiago.moreira@email.com",
                "telefone": "(11) 90987-6543",
                "plano_tipo": "diario",
                "veiculos": [
                    {"placa": "MER1B23", "marca": "Nissan", "modelo": "Kicks Exclusive", "cor": "Cinza Grafite", "tipo": "carro"},
                ],
            },
            {
                "codigo": "CLI-0010",
                "nome": "Camila Ribeiro Duarte",
                "documento": "012.345.678-90",
                "tipo_doc": "CPF",
                "email": "camila.duarte@email.com",
                "telefone": "(11) 99876-5432",
                "plano_tipo": "mensal",
                "veiculos": [
                    {"placa": "DFG7890", "marca": "BMW", "modelo": "320i M Sport", "cor": "Preto", "tipo": "carro"},
                ],
            },
            # 11 a 20 (Novos Clientes Cadastrados)
            {
                "codigo": "CLI-0011",
                "nome": "Rafael Vasconcelos Prado",
                "documento": "113.456.789-83",
                "tipo_doc": "CPF",
                "email": "rafael.prado@email.com",
                "telefone": "(11) 98111-2233",
                "plano_tipo": "mensal",
                "veiculos": [
                    {"placa": "BRA9E99", "marca": "Toyota", "modelo": "Yaris XLS", "cor": "Cinza", "tipo": "carro"},
                    {"placa": "MTO1A23", "marca": "Honda", "modelo": "CB 500F", "cor": "Vermelho", "tipo": "moto"},
                ],
            },
            {
                "codigo": "CLI-0012",
                "nome": "Patrícia Albuquerque Mendes",
                "documento": "123.456.789-09",
                "tipo_doc": "CPF",
                "email": "patricia.mendes@email.com",
                "telefone": "(11) 98222-3344",
                "plano_tipo": "mensal",
                "veiculos": [
                    {"placa": "RIO9B99", "marca": "Volkswagen", "modelo": "T-Cross Highline", "cor": "Branco", "tipo": "carro"},
                ],
            },
            {
                "codigo": "CLI-0013",
                "nome": "Gustavo Henrique Siqueira",
                "documento": "133.456.789-18",
                "tipo_doc": "CPF",
                "email": "gustavo.siqueira@email.com",
                "telefone": "(11) 98333-4455",
                "plano_tipo": "diario",
                "veiculos": [
                    {"placa": "ABC9D88", "marca": "Chevrolet", "modelo": "Tracker Premier", "cor": "Azul", "tipo": "carro"},
                ],
            },
            {
                "codigo": "CLI-0014",
                "nome": "Larissa Nogueira Fonseca",
                "documento": "143.456.789-35",
                "tipo_doc": "CPF",
                "email": "larissa.fonseca@email.com",
                "telefone": "(11) 98444-5566",
                "plano_tipo": "mensal",
                "veiculos": [
                    {"placa": "FLA2C19", "marca": "Hyundai", "modelo": "Creta Ultimate", "cor": "Prata", "tipo": "carro"},
                    {"placa": "FLA3C20", "marca": "Yamaha", "modelo": "MT-03", "cor": "Preto", "tipo": "moto"},
                ],
            },
            {
                "codigo": "CLI-0015",
                "nome": "Bruno Esteves Silveira",
                "documento": "153.456.789-52",
                "tipo_doc": "CPF",
                "email": "bruno.silveira@email.com",
                "telefone": "(11) 98555-6677",
                "plano_tipo": "mensal",
                "veiculos": [
                    {"placa": "SPX4D56", "marca": "Ford", "modelo": "Territory Titanium", "cor": "Preto", "tipo": "carro"},
                ],
            },
            {
                "codigo": "CLI-0016",
                "nome": "Vanessa Toledo Camargo",
                "documento": "163.456.789-70",
                "tipo_doc": "CPF",
                "email": "vanessa.camargo@email.com",
                "telefone": "(11) 98666-7788",
                "plano_tipo": "diario",
                "veiculos": [
                    {"placa": "KLO8J90", "marca": "Renault", "modelo": "Kwid Outsider", "cor": "Laranja", "tipo": "carro"},
                ],
            },
            {
                "codigo": "CLI-0017",
                "nome": "Marcelo Peixoto Barbosa",
                "documento": "173.456.789-97",
                "tipo_doc": "CPF",
                "email": "marcelo.barbosa@email.com",
                "telefone": "(11) 98777-8899",
                "plano_tipo": "mensal",
                "veiculos": [
                    {"placa": "CAR5H67", "marca": "Mercedes-Benz", "modelo": "C300 Sport", "cor": "Cinza", "tipo": "carro"},
                    {"placa": "CAM1E23", "marca": "Mercedes-Benz", "modelo": "Sprinter 415", "cor": "Branco", "tipo": "caminhao"},
                ],
            },
            {
                "codigo": "CLI-0018",
                "nome": "Priscila Antunes Faria",
                "documento": "183.456.789-04",
                "tipo_doc": "CPF",
                "email": "priscila.faria@email.com",
                "telefone": "(11) 98888-9900",
                "plano_tipo": "mensal",
                "veiculos": [
                    {"placa": "ONB2F34", "marca": "Volvo", "modelo": "Marcopolo G7", "cor": "Prata", "tipo": "onibus"},
                ],
            },
            {
                "codigo": "CLI-0019",
                "nome": "Diego Ramalho Moura",
                "documento": "193.456.789-21",
                "tipo_doc": "CPF",
                "email": "diego.moura@email.com",
                "telefone": "(11) 98999-0011",
                "plano_tipo": "diario",
                "veiculos": [
                    {"placa": "MOT8K12", "marca": "BMW", "modelo": "R1250 GS", "cor": "Azul", "tipo": "moto"},
                ],
            },
            {
                "codigo": "CLI-0020",
                "nome": "Isabella Medeiros Barros",
                "documento": "203.456.789-74",
                "tipo_doc": "CPF",
                "email": "isabella.barros@email.com",
                "telefone": "(11) 99111-1223",
                "plano_tipo": "mensal",
                "veiculos": [
                    {"placa": "LUX7M89", "marca": "Audi", "modelo": "Q3 Black Edition", "cor": "Branco", "tipo": "carro"},
                ],
            },
        ]

        novos_clientes = 0
        novos_veiculos = 0
        veiculos_criados = {}

        for item in clientes_data:
            cliente = db.query(Cliente).filter_by(
                estacionamento_id=estacionamento.id,
                documento=item["documento"]
            ).first()

            if not cliente:
                cliente = Cliente(
                    codigo=item["codigo"],
                    estacionamento_id=estacionamento.id,
                    nome=item["nome"],
                    documento=item["documento"],
                    tipo_documento=item["tipo_doc"],
                    email=item["email"],
                    telefone=item["telefone"],
                    plano_tipo=item["plano_tipo"],
                )
                db.add(cliente)
                db.flush()
                novos_clientes += 1
            else:
                if not cliente.codigo:
                    cliente.codigo = item["codigo"]
                cliente.plano_tipo = item["plano_tipo"]
                cliente.telefone = item["telefone"]
                db.add(cliente)
                db.flush()

            for v_data in item["veiculos"]:
                veiculo = db.query(Veiculo).filter_by(
                    estacionamento_id=estacionamento.id,
                    placa=v_data["placa"]
                ).first()

                if not veiculo:
                    veiculo = Veiculo(
                        estacionamento_id=estacionamento.id,
                        cliente_id=cliente.id,
                        placa=v_data["placa"],
                        marca=v_data["marca"],
                        modelo=v_data["modelo"],
                        cor=v_data["cor"],
                        tipo=v_data["tipo"],
                        ativo=True,
                    )
                    db.add(veiculo)
                    db.flush()
                    novos_veiculos += 1

                veiculos_criados[v_data["placa"]] = (veiculo, cliente)

        db.commit()
        print(f"Carga de cadastros: {novos_clientes} novos clientes e {novos_veiculos} novos veículos inseridos.")

        # --- Geração de Movimentações Históricas e Atuais ---
        now = datetime.now(timezone.utc)
        movimentacoes_cenarios = [
            # 1. Movimentação finalizada ontem (BRA2E19 - Carlos Silva)
            {
                "placa": "BRA2E19",
                "delta_entrada_horas": 28,
                "duracao_minutos": 135,
                "esta_estacionado": False,
                "valor": Decimal("25.00"),
            },
            # 2. Movimentação finalizada hoje cedo (BRA2E19 - Carlos Silva)
            {
                "placa": "BRA2E19",
                "delta_entrada_horas": 8,
                "duracao_minutos": 90,
                "esta_estacionado": False,
                "valor": Decimal("20.00"),
            },
            # 3. Movimentação ativa agora (BRA2E19 - Carlos Silva está estacionado!)
            {
                "placa": "BRA2E19",
                "delta_entrada_horas": 1.5,
                "duracao_minutos": None,
                "esta_estacionado": True,
                "valor": None,
            },
            # 4. Movimentação finalizada (ABC1234 - Mariana Santos)
            {
                "placa": "ABC1234",
                "delta_entrada_horas": 24,
                "duracao_minutos": 180,
                "esta_estacionado": False,
                "valor": Decimal("30.00"),
            },
            # 5. Movimentação finalizada (RIO2A18 - Roberto Dias)
            {
                "placa": "RIO2A18",
                "delta_entrada_horas": 12,
                "duracao_minutos": 45,
                "esta_estacionado": False,
                "valor": Decimal("15.00"),
            },
            # 6. Movimentação ativa agora (KGT9082 - Fernanda Lima)
            {
                "placa": "KGT9082",
                "delta_entrada_horas": 2.2,
                "duracao_minutos": None,
                "esta_estacionado": True,
                "valor": None,
            },
            # 7. Movimentação finalizada (XYZ9F88 - Lucas Costa)
            {
                "placa": "XYZ9F88",
                "delta_entrada_horas": 30,
                "duracao_minutos": 60,
                "esta_estacionado": False,
                "valor": Decimal("15.00"),
            },
            # 8. Movimentação finalizada (BRA3A20 - Alexandre Souza)
            {
                "placa": "BRA3A20",
                "delta_entrada_horas": 48,
                "duracao_minutos": 240,
                "esta_estacionado": False,
                "valor": Decimal("35.00"),
            },
            # 9. Movimentação ativa agora (BRA9E99 - Rafael Prado)
            {
                "placa": "BRA9E99",
                "delta_entrada_horas": 0.8,
                "duracao_minutos": None,
                "esta_estacionado": True,
                "valor": None,
            },
            # 10. Movimentação finalizada (RIO9B99 - Patricia Mendes)
            {
                "placa": "RIO9B99",
                "delta_entrada_horas": 16,
                "duracao_minutos": 120,
                "esta_estacionado": False,
                "valor": Decimal("25.00"),
            },
            # 11. Movimentação finalizada (CAR5H67 - Marcelo Barbosa)
            {
                "placa": "CAR5H67",
                "delta_entrada_horas": 6,
                "duracao_minutos": 75,
                "esta_estacionado": False,
                "valor": Decimal("20.00"),
            },
            # 12. Movimentação ativa agora (LUX7M89 - Isabella Barros)
            {
                "placa": "LUX7M89",
                "delta_entrada_horas": 3.0,
                "duracao_minutos": None,
                "esta_estacionado": True,
                "valor": None,
            },
        ]

        novas_movimentacoes = 0
        for cen in movimentacoes_cenarios:
            placa = cen["placa"]
            if placa not in veiculos_criados:
                continue

            veiculo, cliente = veiculos_criados[placa]
            entrada_em = now - timedelta(hours=cen["delta_entrada_horas"])

            # Verificar se já existe movimentação idêntica ou já aberta para a placa
            if cen["esta_estacionado"]:
                existente = db.query(Movimentacao).filter_by(
                    estacionamento_id=estacionamento.id,
                    placa=placa,
                    status=MovimentacaoStatus.ABERTA.value,
                ).first()
            else:
                existente = db.query(Movimentacao).filter_by(
                    estacionamento_id=estacionamento.id,
                    placa=placa,
                    entrada_em=entrada_em,
                ).first()

            if not existente:
                if cen["esta_estacionado"]:
                    status = MovimentacaoStatus.ABERTA.value
                    saida_em = None
                    permanencia = None
                else:
                    status = MovimentacaoStatus.CONCLUIDA.value
                    permanencia = cen["duracao_minutos"]
                    saida_em = entrada_em + timedelta(minutes=permanencia)

                mov = Movimentacao(
                    estacionamento_id=estacionamento.id,
                    veiculo_id=veiculo.id,
                    placa=placa,
                    camera_entrada_id=cam_in.id,
                    camera_saida_id=cam_out.id if not cen["esta_estacionado"] else None,
                    entrada_em=entrada_em,
                    saida_em=saida_em,
                    permanencia_minutos=permanencia,
                    status=status,
                    tipo_cobranca=TipoCobranca.PLANO.value if cliente.plano_tipo == "mensal" else TipoCobranca.AVULSA.value,
                    observacao=f"Entrada registrada via ALPR para {cliente.nome}",
                )
                db.add(mov)
                db.flush()

                if not cen["esta_estacionado"] and cen["valor"]:
                    cobranca = Cobranca(
                        estacionamento_id=estacionamento.id,
                        movimentacao_id=mov.id,
                        cliente_id=cliente.id,
                        valor_bruto=cen["valor"],
                        desconto=Decimal("0.00"),
                        valor_liquido=cen["valor"],
                        status=CobrancaStatus.PAGO.value,
                        data_vencimento=saida_em.date(),
                        criado_em=saida_em,
                    )
                    db.add(cobranca)

                novas_movimentacoes += 1

        db.commit()
        print(f"Carga de movimentações: {novas_movimentacoes} movimentações inseridas com sucesso.")
        print("Base de dados atualizada e pronta para uso no VISORA!")


if __name__ == "__main__":
    seed_data()

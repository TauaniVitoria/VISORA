"""
Serviço de Integração ALPR (Bridge entre Visão Computacional e Regras de Negócio).
Executa o pipeline ALPR sobre fontes de vídeo/câmeras e mapeia passagens confirmadas
em movimentações de entrada e saída no banco de dados com auditoria completa.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple
import uuid
import logging

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from alpr.pipeline import ALPRPipeline, PipelineMetrics
from alpr.tracker import ConfirmedPassageEvent
from app.models.entities import Camera, CameraTipo, Movimentacao, MovimentacaoStatus
from app.schemas.schemas import (
    ALPRConfirmedPassageEventOut,
    ALPRProcessVideoResponse,
    ALPRSimulateDetectionRequest,
    MovimentacaoEntrada,
    MovimentacaoSaida,
)
from app.services.business_services import AuditService, CameraService, MovementService

logger = logging.getLogger("alpr.service")


class ALPRService:
    """
    Orquestrador de integração do ALPR com a camada de negócio e persistência multi-tenant.
    """

    @staticmethod
    def get_pipeline(config_path: Optional[str | Path] = None) -> ALPRPipeline:
        """Instancia o pipeline ALPR a partir da configuração central."""
        if config_path is None:
            config_path = Path("computer-vision/config/alpr_config.yaml")
            if not config_path.exists():
                # Tenta caminho relativo à raiz do projeto
                config_path = Path(__file__).resolve().parents[3] / "computer-vision" / "config" / "alpr_config.yaml"
        return ALPRPipeline(config_path=config_path)

    @staticmethod
    def process_video_file(
        db: Session,
        tenant_id: uuid.UUID,
        video_path: str | Path,
        camera_id: Optional[uuid.UUID] = None,
        sentido_default: Optional[str] = "auto",
        max_frames: Optional[int] = None,
        save_annotated_video: bool = False,
        usuario_id: Optional[uuid.UUID] = None,
    ) -> ALPRProcessVideoResponse:
        """
        Executa o pipeline ALPR sobre um arquivo de vídeo e converte passagens confirmadas
        em movimentações reais no estacionamento.
        """
        v_path = Path(video_path).resolve()
        if not v_path.exists():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Arquivo de vídeo não encontrado no caminho especificado: {video_path}",
            )

        # 1. Carrega câmera, se informada
        camera: Optional[Camera] = None
        if camera_id:
            camera = CameraService.get_camera(db, tenant_id, camera_id)

        # 2. Executa o pipeline de Visão Computacional
        pipeline = ALPRService.get_pipeline()
        output_dir = Path("computer-vision/data/output")
        output_dir.mkdir(parents=True, exist_ok=True)

        confirmed_passages: List[ConfirmedPassageEvent]
        metrics: PipelineMetrics
        confirmed_passages, metrics = pipeline.process_video(
            video_path=v_path,
            output_dir=output_dir,
            max_frames=max_frames,
            save_video=save_annotated_video,
        )

        # 3. Processa cada passagem confirmada no backend
        passages_out: List[ALPRConfirmedPassageEventOut] = []
        movements_count = 0

        for passage in confirmed_passages:
            norm_plate = passage.plate.strip().upper().replace("-", "")
            action = sentido_default.lower() if sentido_default else "auto"

            if camera:
                if camera.tipo == CameraTipo.ENTRADA.value:
                    action = "entrada"
                elif camera.tipo == CameraTipo.SAIDA.value:
                    action = "saida"
                # Se camera.tipo == 'ambos', mantém 'auto'

            # Determinação inteligente quando action for 'auto'
            if action == "auto":
                open_mov = db.scalar(
                    select(Movimentacao).where(
                        Movimentacao.estacionamento_id == tenant_id,
                        Movimentacao.placa == norm_plate,
                        Movimentacao.status == MovimentacaoStatus.ABERTA.value,
                    )
                )
                action = "saida" if open_mov else "entrada"

            movement_id = None
            mov_status = None
            event_type = action

            try:
                if action == "entrada":
                    mov = MovementService.register_entry(
                        db=db,
                        tenant_id=tenant_id,
                        entry_in=MovimentacaoEntrada(
                            placa=norm_plate,
                            camera_id=camera.id if camera else None,
                            timestamp=datetime.now(timezone.utc),
                        ),
                    )
                    movement_id = mov.id
                    mov_status = mov.status
                    movements_count += 1
                elif action == "saida":
                    mov, cobranca = MovementService.register_exit(
                        db=db,
                        tenant_id=tenant_id,
                        exit_in=MovimentacaoSaida(
                            placa=norm_plate,
                            camera_id=camera.id if camera else None,
                            timestamp=datetime.now(timezone.utc),
                        ),
                    )
                    movement_id = mov.id
                    mov_status = mov.status
                    movements_count += 1

            except HTTPException as e:
                # Trata inconsistência ou duplicação sem interromper o restante do lote
                logger.warning(f"Aviso ao registrar passagem ALPR para placa {norm_plate}: {e.detail}")
                event_type = "inconsistente"
                mov_status = "inconsistente"

            # Registra passagem processada
            passage_out = ALPRConfirmedPassageEventOut(
                track_id=passage.track_id,
                plate=passage.plate,
                pattern=passage.pattern,
                vehicle_class=passage.vehicle_class,
                timestamp_sec=passage.timestamp_sec,
                ocr_confidence=passage.ocr_confidence,
                det_confidence=passage.det_confidence,
                tipo_evento=event_type,
                movement_id=movement_id,
                status_movimentacao=mov_status,
            )
            passages_out.append(passage_out)

            # Log de auditoria para o evento de Visão Computacional
            AuditService.log(
                db,
                acao="PASSAGEM_ALPR",
                tabela="movimentacoes",
                registro_id=str(movement_id) if movement_id else f"track_{passage.track_id}",
                tenant_id=tenant_id,
                usuario_id=usuario_id,
                dados_novos={
                    "placa": passage.plate,
                    "padrao": passage.pattern,
                    "classe_veiculo": passage.vehicle_class,
                    "tipo_evento": event_type,
                    "ocr_confidence": passage.ocr_confidence,
                    "camera_id": str(camera.id) if camera else None,
                },
            )

        return ALPRProcessVideoResponse(
            video_source=str(v_path.name),
            total_frames_processed=metrics.total_frames_processed,
            processing_time_seconds=metrics.processing_time_seconds,
            average_fps=metrics.average_fps,
            vehicles_detected_count=metrics.vehicles_detected_count,
            plates_detected_count=metrics.plates_detected_count,
            valid_plates_count=metrics.valid_plates_count,
            invalid_plates_count=metrics.invalid_plates_count,
            confirmed_passages_count=len(confirmed_passages),
            movements_registered=movements_count,
            passages=passages_out,
        )

    @staticmethod
    def simulate_detection(
        db: Session,
        tenant_id: uuid.UUID,
        detection_in: ALPRSimulateDetectionRequest,
        usuario_id: Optional[uuid.UUID] = None,
    ) -> ALPRConfirmedPassageEventOut:
        """
        Processa um evento pontual de detecção (ex: simulação pela interface ou webhook de câmera IP).
        """
        norm_plate = detection_in.placa.strip().upper().replace("-", "")
        camera: Optional[Camera] = None
        if detection_in.camera_id:
            camera = CameraService.get_camera(db, tenant_id, detection_in.camera_id)

        action = (detection_in.tipo_evento or "auto").lower()

        if camera:
            if camera.tipo == CameraTipo.ENTRADA.value:
                action = "entrada"
            elif camera.tipo == CameraTipo.SAIDA.value:
                action = "saida"

        if action == "auto":
            open_mov = db.scalar(
                select(Movimentacao).where(
                    Movimentacao.estacionamento_id == tenant_id,
                    Movimentacao.placa == norm_plate,
                    Movimentacao.status == MovimentacaoStatus.ABERTA.value,
                )
            )
            action = "saida" if open_mov else "entrada"

        movement_id = None
        mov_status = None
        event_time = detection_in.timestamp or datetime.now(timezone.utc)

        if action == "entrada":
            mov = MovementService.register_entry(
                db=db,
                tenant_id=tenant_id,
                entry_in=MovimentacaoEntrada(
                    placa=norm_plate,
                    camera_id=camera.id if camera else None,
                    timestamp=event_time,
                ),
            )
            movement_id = mov.id
            mov_status = mov.status
        else:
            mov, _ = MovementService.register_exit(
                db=db,
                tenant_id=tenant_id,
                exit_in=MovimentacaoSaida(
                    placa=norm_plate,
                    camera_id=camera.id if camera else None,
                    timestamp=event_time,
                ),
            )
            movement_id = mov.id
            mov_status = mov.status

        AuditService.log(
            db,
            acao="DETECCAO_ALPR_SIMULADA",
            tabela="movimentacoes",
            registro_id=str(movement_id),
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            dados_novos={
                "placa": norm_plate,
                "tipo_evento": action,
                "ocr_confidence": detection_in.ocr_confidence,
                "camera_id": str(camera.id) if camera else None,
            },
        )

        return ALPRConfirmedPassageEventOut(
            track_id=1,
            plate=norm_plate,
            pattern="mercosul",
            vehicle_class="carro",
            timestamp_sec=0.0,
            ocr_confidence=detection_in.ocr_confidence,
            det_confidence=detection_in.det_confidence,
            tipo_evento=action,
            movement_id=movement_id,
            status_movimentacao=mov_status,
        )


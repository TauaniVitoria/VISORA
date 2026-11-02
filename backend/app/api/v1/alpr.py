"""
Rotas REST para Ingestão e Processamento ALPR (Computer Vision Engine).
"""

from pathlib import Path
import shutil
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, get_tenant_id, require_roles
from app.models.entities import Usuario, UsuarioPerfil
from app.schemas.schemas import (
    ALPRConfirmedPassageEventOut,
    ALPRProcessVideoResponse,
    ALPRSimulateDetectionRequest,
)
from app.services.alpr_service import ALPRService

router = APIRouter(
    prefix="/alpr",
    tags=["Processamento ALPR"],
    dependencies=[Depends(require_roles(UsuarioPerfil.ESTACIONAMENTO_ADMIN, UsuarioPerfil.SAAS_ADMIN))],
)


ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}


@router.post("/process-video", response_model=ALPRProcessVideoResponse)
async def process_video(
    video_file: Optional[UploadFile] = File(None),
    video_path: Optional[str] = Form(None),
    camera_id: Optional[uuid.UUID] = Form(None),
    sentido_default: str = Form("auto"),
    max_frames: Optional[int] = Form(None),
    save_annotated_video: bool = Form(False),
    db: Session = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Executa o pipeline ALPR sobre um arquivo de vídeo enviado ou existente no disco.
    As passagens de veículos e placas confirmadas são automaticamente persistidas
    como entradas ou saídas para o estacionamento autenticado.
    """
    target_path: Path

    if video_file is not None and video_file.filename:
        safe_filename = Path(video_file.filename).name
        ext = Path(safe_filename).suffix.lower()
        if ext not in ALLOWED_VIDEO_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Formato de arquivo não permitido ({ext}). Use: {', '.join(sorted(ALLOWED_VIDEO_EXTENSIONS))}.",
            )
        upload_dir = Path("computer-vision/data/input/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        unique_name = f"{uuid.uuid4()}_{safe_filename}"
        target_path = upload_dir / unique_name

        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(video_file.file, buffer)
    elif video_path:
        if ".." in Path(video_path).parts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Caminho de vídeo inválido (path traversal não permitido).",
            )
        target_path = Path(video_path)
        if target_path.suffix.lower() not in ALLOWED_VIDEO_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Extensão de vídeo inválida ({target_path.suffix}).",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="É necessário fornecer um arquivo de vídeo (upload) ou o parâmetro 'video_path'.",
        )

    return ALPRService.process_video_file(
        db=db,
        tenant_id=tenant_id,
        video_path=target_path,
        camera_id=camera_id,
        sentido_default=sentido_default,
        max_frames=max_frames,
        save_annotated_video=save_annotated_video,
        usuario_id=current_user.id,
    )


@router.post("/simulate-detection", response_model=ALPRConfirmedPassageEventOut)
def simulate_detection(
    detection_in: ALPRSimulateDetectionRequest,
    db: Session = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Simula uma detecção de placa em tempo real proveniente de uma câmera de cancela ou webhook.
    Determina automaticamente se é entrada ou saída e atualiza o estado operacional.
    """
    return ALPRService.simulate_detection(
        db=db,
        tenant_id=tenant_id,
        detection_in=detection_in,
        usuario_id=current_user.id,
    )


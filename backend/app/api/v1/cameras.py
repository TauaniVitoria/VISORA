"""
Rotas REST para Gestão de Câmeras de Reconhecimento ALPR.
"""

from typing import List
import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_tenant_id, get_current_user, get_db
from app.models.entities import Usuario
from app.schemas.schemas import CameraCreate, CameraOut, CameraUpdate
from app.services.business_services import CameraService

router = APIRouter(prefix="/cameras", tags=["Câmeras ALPR"])


@router.get("/", response_model=List[CameraOut])
def list_cameras(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    current_user: Usuario = Depends(get_current_user),
):
    """Lista todas as câmeras cadastradas para o estacionamento atual."""
    return CameraService.list_cameras(db, tenant_id=tenant_id, skip=skip, limit=limit)


@router.post("/", response_model=CameraOut, status_code=status.HTTP_201_CREATED)
def create_camera(
    camera_in: CameraCreate,
    db: Session = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    current_user: Usuario = Depends(get_current_user),
):
    """Cadastra uma nova câmera vinculada ao estacionamento."""
    return CameraService.create_camera(
        db,
        tenant_id=tenant_id,
        camera_in=camera_in,
        usuario_id=current_user.id,
    )


@router.get("/{camera_id}", response_model=CameraOut)
def get_camera(
    camera_id: uuid.UUID,
    db: Session = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    current_user: Usuario = Depends(get_current_user),
):
    """Obtém detalhes de uma câmera específica."""
    return CameraService.get_camera(db, tenant_id=tenant_id, camera_id=camera_id)


@router.put("/{camera_id}", response_model=CameraOut)
def update_camera(
    camera_id: uuid.UUID,
    camera_in: CameraUpdate,
    db: Session = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    current_user: Usuario = Depends(get_current_user),
):
    """Atualiza configurações ou estado de uma câmera."""
    return CameraService.update_camera(
        db,
        tenant_id=tenant_id,
        camera_id=camera_id,
        camera_in=camera_in,
        usuario_id=current_user.id,
    )


@router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_camera(
    camera_id: uuid.UUID,
    db: Session = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    current_user: Usuario = Depends(get_current_user),
):
    """Remove uma câmera do estacionamento."""
    CameraService.delete_camera(
        db,
        tenant_id=tenant_id,
        camera_id=camera_id,
        usuario_id=current_user.id,
    )
    return None
